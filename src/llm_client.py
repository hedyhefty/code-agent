import logging
import os
import json
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from openai import AsyncOpenAI

from .history_manager import HistoryManager
from .mcp_client import MCPClient

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
        self.max_history = 100
        self.max_steps = 20

        # 实例化，但不立即启动连接
        self.mcp_client = MCPClient()

    async def startup(self):
        """异步启动所有 MCP Servers"""
        await self.mcp_client.load_tools()

    async def chat_stream(self, user_input: str, system_prompt: str = None) -> AsyncGenerator[str, None]:
        if not self.history.current_session_id:
            self.history.start_new_session(system_prompt)

        self.history.save_message("user", user_input)

        current_step = 0
        while current_step < self.max_steps:
            current_step += 1
            logger.info(f"开始第 {current_step} 轮推理")

            try:
                context = self.history.get_context()[-self.max_history:]

                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=context,
                    stream=True,
                    tools=self.mcp_client.get_schemas() or None,  # 如果没有工具，传 None 以防 API 报错
                    tool_choice="auto" if self.mcp_client.get_schemas() else "none"
                )

                full_response_content = ""
                tool_calls_buffer = {}
                thinking_cleared = False

                async for chunk in response:
                    logger.info(f"第{current_step}轮推理：{chunk}")
                    if not thinking_cleared:
                        thinking_cleared = True
                        yield "<CLEAR_THINKING>"

                    delta = chunk.choices[0].delta

                    if delta.content:
                        full_response_content += delta.content
                        yield delta.content

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

                if tool_calls_buffer:
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

                    for tc in formatted_tool_calls:
                        func_name = tc["function"]["name"]
                        args = tc["function"]["arguments"]

                        yield f"\n\n> ⚙️ **执行工具**: `{func_name}`\n\n"

                        # --- 核心改动：使用 await 调用异步的 MCP 通信 ---
                        result = await self.mcp_client.call_tool(func_name, args)

                        self.history.save_message(
                            role="tool",
                            content=str(result),
                            tool_call_id=tc["id"],
                            name=func_name
                        )

                    continue

                else:
                    if full_response_content:
                        self.history.save_message("assistant", full_response_content)
                    break

            except Exception as e:
                logger.error(f"推理循环异常: {str(e)}", exc_info=True)
                yield f"\n[系统错误]: {str(e)}"
                break

        if current_step >= self.max_steps:
            yield "\n\n[提示]: 已达到最大推理步数，自动停止。"
