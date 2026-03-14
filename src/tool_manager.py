import os
import importlib
import inspect
import json
import logging
from typing import Dict, List
from .base_tool import BaseTool

logger = logging.getLogger(__name__)


class ToolManager:
    def __init__(self, tools_dir: str = "tools"):
        self.tools_dir = tools_dir
        self._tools: Dict[str, BaseTool] = {}
        logger.info(f"初始化 ToolManager，工具目录: {tools_dir}")
        self.load_tools()

    def load_tools(self):
        """
        动态扫描 tools 目录并加载继承了 BaseTool 的类
        """
        logger.info(f"正在扫描工具目录: {self.tools_dir}")
        
        if not os.path.exists(self.tools_dir):
            logger.warning(f"工具目录不存在，创建目录: {self.tools_dir}")
            os.makedirs(self.tools_dir)
            return

        # 获取所有 Python 文件
        for filename in os.listdir(self.tools_dir):
            if filename.endswith(".py") and filename != "base_tool.py" and not filename.startswith("__"):
                module_name = f"{self.tools_dir}.{filename[:-3]}"
                try:
                    # 动态导入模块
                    module = importlib.import_module(module_name)
                    # 重新加载模块以支持热更新（可选）
                    importlib.reload(module)

                    # 寻找 BaseTool 的子类
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, BaseTool) and obj is not BaseTool:
                            instance = obj()
                            self._tools[instance.name] = instance
                            logger.info(f"已加载工具: {instance.name}")
                except Exception as e:
                    logger.error(f"加载工具 {filename} 失败: {str(e)}", exc_info=True)
        
        logger.info(f"工具加载完成，共加载 {len(self._tools)} 个工具")

    def get_schemas(self) -> List[dict]:
        """获取所有工具的 OpenAI Schema 定义"""
        return [tool.to_openai_schema() for tool in self._tools.values()]

    def call_tool(self, name: str, arguments_json: str) -> str:
        """
        根据 AI 的指令调用对应工具
        """
        tool = self._tools.get(name)
        if not tool:
            logger.error(f"工具未找到: {name}")
            return f"错误: 工具 '{name}' 未找到。"

        try:
            # 解析 AI 传回的 JSON 字符串参数
            args = json.loads(arguments_json) if arguments_json else {}
            logger.info(f"执行工具: {name}, 参数: {args}")
            result = tool.execute(**args)
            logger.info(f"工具执行结果: {result[:100]}..." if len(result) > 100 else f"工具执行结果: {result}")
            return result
        except Exception as e:
            logger.error(f"执行工具失败: {name}, 错误: {str(e)}", exc_info=True)
            return f"执行工具 '{name}' 时出错: {str(e)}"