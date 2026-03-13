from abc import ABC, abstractmethod


class BaseTool(ABC):
    """
    所有工具的抽象基类。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称，必须是英文下划线格式，如 get_current_time"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述，给 AI 解释什么时候该用这个工具"""
        pass

    @property
    def parameters(self) -> dict:
        """
        工具参数的 JSON Schema 定义。
        默认返回空参数列表。如果工具需要参数，请重写此方法。
        """
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """
        真正的业务逻辑执行处。
        """
        pass

    def to_openai_schema(self) -> dict:
        """
        将工具转换为 OpenAI API 要求的格式。
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }