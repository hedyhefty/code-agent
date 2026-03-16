import json
import logging
import os
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Dict, List

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClient:
    def __init__(self):
        self._exit_stack = AsyncExitStack()
        # 统一缓存所有的工具定义 (名称 -> {"schema": OpenAI格式, "session": 对应的MCP连接})
        self._tool_registry: Dict[str, dict] = {}
        logger.info("MCP Client核心已启动")

    def get_project_root(self) -> Path:
        """自动向上搜索，直到找到包含 mcp_config.json 的根目录"""
        # 从当前脚本所在位置开始向上搜索
        current_path = Path(__file__).resolve().parent

        # 向上寻找直到找到根目录（例如通过查找 .git 或特定的配置文件）
        # 这里我们查找 config 所在的目录
        for parent in [current_path] + list(current_path.parents):
            if (parent / "mcp_config.json").exists():
                return parent

        # 如果找不到，返回当前目录作为兜底
        return current_path

    async def load_tools(self, config_filename: str = "mcp_config.json"):
        """读取配置并连接所有 MCP Servers"""
        project_root = self.get_project_root()
        # 2. 拼接出配置文件的绝对路径
        # 如果你的配置文件就在项目根目录下
        config_path = project_root / config_filename
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                # 1. 读取原始字符串
                config_str = f.read()

                # 2. 执行替换 (确保 .env 里的变量已加载，因为你在 llm_client.py 顶部已经 load_dotenv() 了)
                # 注意：这里我们替换所有匹配的占位符
                if "${AGENT_WORKSPACE}" in config_str:
                    workspace = os.getcwd()
                    if not workspace:
                        raise ValueError(f"设置工作区间异常，os.getcwd()={os.getcwd()}")
                    config_str = config_str.replace("${AGENT_WORKSPACE}", workspace)

                if "${PROJECT_DIR}" in config_str:
                    project_dir = os.getenv("PROJECT_DIR")
                    if not project_dir:
                        raise ValueError("环境变量 PROJECT_DIR 未设置，请在 .env 中配置它")
                    config_str = config_str.replace("${PROJECT_DIR}", project_dir)

                # 3. 将替换后的字符串转为字典
                config = json.loads(config_str)
        except FileNotFoundError:
            logger.warning(f"未找到配置文件 {config_path}，当前无工具可用。")
            return

        for server_name, server_info in config.get("mcpServers", {}).items():
            await self.connect_mcp_server(
                server_name=server_name,
                command=server_info["command"],
                args=server_info["args"]
            )

        logger.info(f"工具加载完成，共挂载 {len(self._tool_registry)} 个工具")

    async def connect_mcp_server(self, server_name: str, command: str, args: List[str]):
        """连接单个 MCP Server 并提取工具 Schema"""
        logger.info(f"正在启动 MCP Server [{server_name}]: {command} {' '.join(args)}")
        server_params = StdioServerParameters(command=command, args=args)

        try:
            # 1. 建立 stdio 传输通道
            stdio_transport = await self._exit_stack.enter_async_context(stdio_client(server_params))
            read, write = stdio_transport

            # 2. 建立 MCP Session
            session = await self._exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()

            # 3. 获取该 Server 支持的所有工具
            mcp_tools = await session.list_tools()

            # 4. 将 MCP Schema 无缝转为 OpenAI Schema 并注册
            for tool in mcp_tools.tools:
                openai_schema = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema
                    }
                }
                self._tool_registry[tool.name] = {
                    "schema": openai_schema,
                    "session": session
                }
                logger.info(f"已注册 MCP 工具: {tool.name} (来自 {server_name})")

        except Exception as e:
            logger.error(f"连接 MCP Server [{server_name}] 失败: {str(e)}", exc_info=True)

    def get_schemas(self) -> List[dict]:
        """获取所有工具的 OpenAI Schema 定义"""
        return [meta["schema"] for meta in self._tool_registry.values()]

    async def call_tool(self, name: str, arguments_json: str) -> str:
        """根据 AI 的指令通过 MCP 协议跨进程调用工具"""
        if name not in self._tool_registry:
            logger.error(f"工具未找到: {name}")
            return f"错误: 工具 '{name}' 未找到。"

        tool_meta = self._tool_registry[name]
        session: ClientSession = tool_meta["session"]
        args = json.loads(arguments_json) if arguments_json else {}

        try:
            logger.info(f"执行 MCP 工具: {name}, 参数: {args}")
            # 发起 JSON-RPC 调用
            result = await session.call_tool(name, arguments=args)

            # 解析 MCP 的标准返回格式
            if result.content:
                # 通常提取第一段文本内容
                output = result.content[0].text
                logger.info(f"工具执行结果: {output[:100]}..." if len(output) > 100 else f"工具执行结果: {output}")
                return output
            return "执行成功，无返回值。"

        except Exception as e:
            logger.error(f"执行工具失败: {name}, 错误: {str(e)}", exc_info=True)
            return f"执行工具 '{name}' 时出错: {str(e)}"

    async def close(self):
        """安全释放所有子进程"""
        await self._exit_stack.aclose()
        logger.info("已断开所有 MCP Server 连接")
