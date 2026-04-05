import json
import os
from datetime import datetime
from typing import Any, List, Optional, Dict


class HistoryManager:
    MAX_MESSAGES = 1000

    def __init__(self, storage_dir: str = "history") -> None:
        project_dir = os.getenv("PROJECT_DIR")
        self.storage_dir: str = f"{project_dir}/{storage_dir}"
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
        self.current_session_id: Optional[str] = None
        self.current_messages: List[Dict[str, Any]] = []

    def start_new_session(self, system_prompt: Optional[str] = None) -> str:
        self.current_session_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.current_messages = []
        if system_prompt:
            self.current_messages.append({"role": "system", "content": system_prompt})
        return self.current_session_id

    def save_message(
            self,
            role: str,
            content: Optional[str] = None,
            tool_calls: Optional[List[Dict[str, Any]]] = None,
            tool_call_id: Optional[str] = None,
            name: Optional[str] = None,
    ) -> None:
        message: Dict[str, Any] = {
            "role": role,
            "timestamp": datetime.now().isoformat(),
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

        if len(self.current_messages) > self.MAX_MESSAGES:
            first_non_system = 0
            for i, msg in enumerate(self.current_messages):
                if msg.get("role") != "system":
                    first_non_system = i
                    break
            keep_count = self.MAX_MESSAGES - 1
            if first_non_system < keep_count:
                self.current_messages = self.current_messages[:1] + self.current_messages[-(keep_count):]
            else:
                self.current_messages = self.current_messages[first_non_system:]

        if self.current_session_id:
            file_path = os.path.join(self.storage_dir, f"{self.current_session_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(
                    {"session_id": self.current_session_id, "messages": self.current_messages},
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

    def get_context(self) -> List[Dict[str, Any]]:
        api_messages: List[Dict[str, Any]] = []
        for msg in self.current_messages:
            api_msg = {k: v for k, v in msg.items() if k in ['role', 'content', 'tool_calls', 'tool_call_id', 'name']}
            api_messages.append(api_msg)
        return api_messages

    def list_sessions(self) -> List[str]:
        return [f.replace(".json", "") for f in os.listdir(self.storage_dir) if f.endswith(".json")]

    def load_session(self, session_id: str) -> bool:
        file_path = os.path.join(self.storage_dir, f"{session_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.current_session_id = session_id
                self.current_messages = data["messages"]
                return True
        return False
