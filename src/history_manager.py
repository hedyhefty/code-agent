import json
import os
from datetime import datetime
from typing import List, Dict

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

    def save_message(self, role, content):
        self.current_messages.append({"role": role, "content": content, "timestamp": datetime.now().isoformat()})
        if self.current_session_id:
            file_path = os.path.join(self.storage_dir, f"{self.current_session_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({"session_id": self.current_session_id, "messages": self.current_messages}, f, indent=2, ensure_ascii=False)

    def list_sessions(self) -> List[str]:
        return [f.replace(".json","") for f in os.listdir(self.storage_dir) if f.endswith(".json")]

    def load_session(self, session_id):
        file_path = os.path.join(self.storage_dir, f"{session_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.current_session_id = session_id
                self.current_messages = data["messages"]
                return True
        return False