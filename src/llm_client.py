import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from openai import AsyncOpenAI

from src.history_manager import HistoryManager

# 加载环境变量
load_dotenv()


class LLMClient:
    def __init__(self):
        # 从环境变量初始化配置
        api_key = os.getenv("LLM_API_KEY")
        base_url = os.getenv("LLM_BASE_URL")
        model = os.getenv("LLM_MODEL")

        if not api_key:
            raise ValueError("LLM_API_KEY 未设置，请检查 .env 文件")

        # 初始化异步客户端
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

        # 引入历史管理器
        self.history = HistoryManager(storage_dir="history")
        self.max_history = 20  # 滑动窗口限制

    async def chat_stream(self, user_input: str, system_prompt: str = None) -> AsyncGenerator[str, None]:
        """
        处理流式对话的核心逻辑
        """
        # 1. 确保有会话，没有则开启一个
        if not self.history.current_session_id:
            self.history.start_new_session(system_prompt)

        # 2. 保存用户输入到历史记录
        self.history.save_message("user", user_input)

        try:
            # 3. 准备消息上下文（使用滑动窗口截取最近 N 条）
            context = self.history.current_messages[-self.max_history:]

            # 4. 异步调用 API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=context,
                stream=True,
                max_tokens=2000,
                temperature=0.7
            )

            full_response = []

            # 5. 异步迭代流式结果
            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    full_response.append(content)
                    yield content

            # 6. 保存助手回答到历史记录
            if full_response:
                assistant_reply = "".join(full_response)
                self.history.save_message("assistant", assistant_reply)

        except Exception as e:
            yield f"\n[API调用错误]: {str(e)}"
