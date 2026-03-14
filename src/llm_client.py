import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from openai import AsyncOpenAI

from .history_manager import HistoryManager
from .tool_manager import ToolManager

# 加载环境变量
load_dotenv()


class LLMClient:
    def __init__(self):
        api_key = os.getenv("LLM_API_KEY")
        base_url = os.getenv("LLM_BASE_URL")
        model = os.getenv("LLM_MODEL")

        if not api_key:
            raise ValueError("LLM_API_KEY 未设置，请检查 .env 文件")

        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.history = HistoryManager(storage_dir="history")
        self.max_history = 20
        self.tool_manager = ToolManager()

    async def chat_stream(self, user_input: str, system_prompt: str = None) -> AsyncGenerator[str, None]:
        if not self.history.current_session_id:
            self.history.start_new_session(system_prompt)

        self.history.save_message("user", user_input)

        try:
            context = self.history.get_context()[-self.max_history:]

            # 开启流式 API 调用
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=context,
                stream=True,
                tools=self.tool_manager.get_schemas(),
                tool_choice="auto"
            )

            full_response_content = ""
            tool_calls_buffer = {}  # 用于暂存流式传回的工具信息
            thinking_cleared = False

            async for chunk in response:
                if not thinking_cleared:
                    thinking_cleared = True
                    yield "<CLEAR_THINKING>"
                delta = chunk.choices[0].delta

                # 情况 A：处理普通文本流
                if delta.content:
                    full_response_content += delta.content
                    yield delta.content

                # 情况 B：处理工具调用流（碎片化的）
                elif delta.tool_calls:
                    for tc_chunk in delta.tool_calls:
                        idx = tc_chunk.index
                        if idx not in tool_calls_buffer:
                            tool_calls_buffer[idx] = {
                                "id": tc_chunk.id,
                                "name": tc_chunk.function.name,
                                "arguments": ""
                            }
                        if tc_chunk.function.arguments:
                            tool_calls_buffer[idx]["arguments"] += tc_chunk.function.arguments

            # --- 流式读取结束，开始判定后续动作 ---

            if tool_calls_buffer:
                # 1. 构造标准的 tool_calls 格式存入历史
                formatted_tool_calls = []
                for _, tc in tool_calls_buffer.items():
                    formatted_tool_calls.append({
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["arguments"]}
                    })

                self.history.save_message(role="assistant", content=full_response_content or None,
                                          tool_calls=formatted_tool_calls)

                # 2. 执行工具
                for tc in formatted_tool_calls:
                    func_name = tc["function"]["name"]
                    args = tc["function"]["arguments"]
                    yield f"\n\n> ⚙️ **调用本地工具**: `{func_name}`\n\n"

                    result = self.tool_manager.call_tool(func_name, args)
                    self.history.save_message(role="tool", content=str(result), tool_call_id=tc["id"], name=func_name)

                # 3. 递归调用自身：让 AI 根据工具结果再次生成回答（这次依然是流式的）
                # 这里不需要传 user_input，因为信息已经在 history 里了
                async for final_chunk in self.chat_stream_recursive():
                    yield final_chunk
            else:
                # 普通对话结束，保存历史
                if full_response_content:
                    self.history.save_message("assistant", full_response_content)

        except Exception as e:
            yield f"\n[API调用错误]: {str(e)}"

    async def chat_stream_recursive(self) -> AsyncGenerator[str, None]:
        """专门用于处理工具执行后的第二次流式调用"""
        context = self.history.get_context()[-self.max_history:]
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=context,
            stream=True
        )
        full_text = ""
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                full_text += content
                yield content
        if full_text:
            self.history.save_message("assistant", full_text)
