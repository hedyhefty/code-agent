import json
import os
from datetime import datetime
from typing import List


class HistoryManager:
    def __init__(self, storage_dir="history"):
        self.storage_dir = storage_dir
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
        self.current_session_id = None
        self.current_messages = []

    def start_new_session(self, system_prompt=None):
        self.current_session_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.current_messages = []
        if system_prompt:
            self.current_messages.append({"role": "system", "content": system_prompt})
        return self.current_session_id

    def save_message(self, role, content=None, tool_calls=None, tool_call_id=None, name=None):
        """保存消息，兼容工具调用的所有必需字段"""
        message = {
            "role": role,
            "timestamp": datetime.now().isoformat()
        }

        if content is not None:
            message["content"] = content
        if tool_calls:
            message["tool_calls"] = tool_calls
        if tool_call_id:
            message["tool_call_id"] = tool_call_id
        if name:
            message["name"] = name

        self.current_messages.append(message)

        if self.current_session_id:
            file_path = os.path.join(self.storage_dir, f"{self.current_session_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({"session_id": self.current_session_id, "messages": self.current_messages}, f, indent=2,
                          ensure_ascii=False)

    def get_context(self) -> List[dict]:
        """专门为 API 提供干净的上下文（过滤掉 timestamp）"""
        api_messages = []
        for msg in self.current_messages:
            # 只保留 OpenAI 认识的字段
            api_msg = {k: v for k, v in msg.items() if k in ['role', 'content', 'tool_calls', 'tool_call_id', 'name']}
            api_messages.append(api_msg)
        return api_messages

    def list_sessions(self) -> List[str]:
        return [f.replace(".json", "") for f in os.listdir(self.storage_dir) if f.endswith(".json")]

    def load_session(self, session_id):
        file_path = os.path.join(self.storage_dir, f"{session_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.current_session_id = session_id
                self.current_messages = data["messages"]
                return True
        return False
