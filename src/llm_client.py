import logging
import os
import json
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from openai import AsyncOpenAI

from .history_manager import HistoryManager
from .tool_manager import ToolManager

# 加载环境变量
load_dotenv()
logger = logging.getLogger(__name__)


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
        # 设置最大推理步数，防止工具调用进入死循环
        self.max_steps = 5

    async def chat_stream(self, user_input: str, system_prompt: str = None) -> AsyncGenerator[str, None]:
        """使用 ReAct 循环架构的流式对话实现"""
        if not self.history.current_session_id:
            self.history.start_new_session(system_prompt)

        self.history.save_message("user", user_input)

        current_step = 0
        while current_step < self.max_steps:
            current_step += 1
            logger.info(f"开始第 {current_step} 轮推理")

            try:
                context = self.history.get_context()[-self.max_history:]

                # 只有在第一轮推理时尝试请求工具
                # 后续轮次中模型会根据历史记录（包含 tool 结果）决定是否继续用工具
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=context,
                    stream=True,
                    tools=self.tool_manager.get_schemas(),
                    tool_choice="auto"
                )

                full_response_content = ""
                tool_calls_buffer = {}
                thinking_cleared = False

                async for chunk in response:
                    logger.info(f"第{current_step}轮推理：{chunk}")
                    # 配合 UI 擦除“思考中”状态
                    if not thinking_cleared:
                        thinking_cleared = True
                        yield "<CLEAR_THINKING>"

                    delta = chunk.choices[0].delta

                    # 处理文本流
                    if delta.content:
                        full_response_content += delta.content
                        yield delta.content

                    # 处理工具调用流
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

                # --- 判定当前轮次动作 ---

                if tool_calls_buffer:
                    # 1. 整理并保存助手发送的工具调用意图
                    formatted_tool_calls = []
                    for _, tc in tool_calls_buffer.items():
                        formatted_tool_calls.append({
                            "id": tc["id"],
                            "type": "function",
                            "function": {"name": tc["name"], "arguments": tc["arguments"]}
                        })

                    self.history.save_message(
                        role="assistant",
                        content=full_response_content or None,
                        tool_calls=formatted_tool_calls
                    )

                    # 2. 依次执行工具并保存结果
                    for tc in formatted_tool_calls:
                        func_name = tc["function"]["name"]
                        args = tc["function"]["arguments"]

                        yield f"\n\n> ⚙️ **执行工具**: `{func_name}`\n\n"
                        logger.info(f"正在执行本地工具: {func_name}, 参数: {args}")

                        # 执行并保存结果到历史记录，以便下一轮推理使用
                        result = self.tool_manager.call_tool(func_name, args)
                        self.history.save_message(
                            role="tool",
                            content=str(result),
                            tool_call_id=tc["id"],
                            name=func_name
                        )

                    # 关键点：执行完工具后，不 break，继续下一轮 while 循环让 AI 总结结果
                    continue

                else:
                    # 如果没有工具调用，说明 AI 已经给出了最终答复
                    if full_response_content:
                        self.history.save_message("assistant", full_response_content)
                    break  # 退出推理循环

            except Exception as e:
                logger.error(f"推理循环异常: {str(e)}", exc_info=True)
                yield f"\n[系统错误]: {str(e)}"
                break

        if current_step >= self.max_steps:
            yield "\n\n[提示]: 已达到最大推理步数，自动停止。"
