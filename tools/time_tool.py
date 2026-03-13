from datetime import datetime
from src.base_tool import BaseTool

class TimeTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_current_time"

    @property
    def description(self) -> str:
        return "获取当前的系统时间。当用户询问时间、日期、星期几或今天几号时非常有用。"

    def execute(self, **kwargs) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")