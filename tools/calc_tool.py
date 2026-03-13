from src.base_tool import BaseTool


class CalculatorTool(BaseTool):
    @property
    def name(self):
        return "calculator"

    @property
    def description(self):
        return "用于进行数学计算，例如加减乘除。"

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "要计算的数学表达式，如 '2 + 3'"}
            },
            "required": ["expression"]
        }

    def execute(self, expression: str):
        try:
            # 安全警告：在生产环境建议使用 numexpr 或 ast.literal_eval
            result = eval(expression)
            return str(result)
        except Exception as e:
            return f"计算错误: {e}"
