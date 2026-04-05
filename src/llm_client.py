import asyncio
import logging
import os
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from .history_manager import HistoryManager
from .mcp_client import MCPClient

logger = logging.getLogger(__name__)

# API 重试配置
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2  # 指数退避基数（秒）


def _is_retryable_error(e: Exception) -> bool:
    """判断错误是否值得重试（网络超时类错误）"""
    error_str = str(e).lower()
    retryable_keywords = [
        "timeout", "timed out", "request timeout",
        "connection", "network", "refused",
        "reset", "broken pipe", "temporarily unavailable"
    ]
    # 429 Rate Limit 也值得重试
    if "429" in error_str or "rate limit" in error_str:
        return True
    return any(kw in error_str for kw in retryable_keywords)


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

            retry_count = 0
            response = None

            # API 调用重试循环
            while retry_count < MAX_RETRIES:
                try:
                    context = self.history.get_context()[-self.max_history:]

                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=context,
                        stream=True,
                        tools=self.mcp_client.get_schemas() or None,
                        tool_choice="auto" if self.mcp_client.get_schemas() else "none",
                        timeout=300  # 5分钟超时，防止 API 卡死
                    )
                    break  # 成功则跳出重试循环

                except Exception as e:
                    if retry_count == MAX_RETRIES - 1 or not _is_retryable_error(e):
                        # 最后一次失败或不可重试的错误
                        logger.error(f"推理循环异常: {str(e)}", exc_info=True)
                        yield f"\n[系统错误]: {str(e)}"
                        response = None
                        break

                    retry_count += 1
                    delay = RETRY_BASE_DELAY * (2 ** (retry_count - 1))
                    logger.warning(f"API 调用失败 ({retry_count}/{MAX_RETRIES})，{delay}s 后重试: {str(e)}")
                    await asyncio.sleep(delay)

            if response is None:
                break  # 重试全部失败后退出循环

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

        if current_step >= self.max_steps:
            yield "\n\n[提示]: 已达到最大推理步数，自动停止。"
