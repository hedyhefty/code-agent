import os
from typing import List, Dict, AsyncGenerator
from openai import AsyncOpenAI  # 改为异步客户端
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self):
        api_key = os.getenv("LLM_API_KEY")
        base_url = os.getenv("LLM_BASE_URL")
        model = os.getenv("LLM_MODEL")
        
        if not api_key:
            raise ValueError("LLM_API_KEY未设置，请检查.env文件")
        
        # 初始化异步客户端
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.messages: List[Dict[str, str]] = []
        self.max_history = 20  # 设置最大历史轮数

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        # 简易滑动窗口：保留最新的消息，但如果第一条是system则始终保留
        if len(self.messages) > self.max_history:
            has_system = self.messages[0]["role"] == "system"
            if has_system:
                self.messages = [self.messages[0]] + self.messages[-(self.max_history-1):]
            else:
                self.messages = self.messages[-self.max_history:]

    def clear_messages(self) -> None:
        self.messages = []

    async def chat_stream(self, user_input: str, system_prompt: str = None) -> AsyncGenerator[str, None]:
        # 1. 初始化系统提示词
        if system_prompt and not any(m["role"] == "system" for m in self.messages):
            self.messages.insert(0, {"role": "system", "content": system_prompt})
        
        # 2. 添加用户输入
        self.add_message("user", user_input)
        
        try:
            # 3. 异步调用 API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                stream=True,
                max_tokens=2000,
                temperature=0.7
            )
            
            full_response = []
            # 4. 异步迭代流式结果
            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    full_response.append(content)
                    yield content
            
            # 5. 保存助手回答
            if full_response:
                self.add_message("assistant", "".join(full_response))
                
        except Exception as e:
            yield f"API调用错误: {str(e)}"