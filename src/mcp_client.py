import json
import logging
import os
import time
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClient:
    def __init__(self) -> None:
        self._exit_stack = AsyncExitStack()
        self._tool_registry: Dict[str, Dict[str, Any]] = {}
        logger.info("MCP Client核心已启动")

    def get_project_root(self) -> Path:
        current_path = Path(__file__).resolve().parent
        for parent in [current_path] + list(current_path.parents):
            if (parent / "mcp_config.json").exists():
                return parent
        return current_path

    async def load_tools(self, config_filename: str = "mcp_config.json") -> None:
        project_root = os.getenv("PROJECT_ROOT")
        config_path = f"{project_root}/{config_filename}"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_str = f.read()

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

                config = json.loads(config_str)
        except FileNotFoundError:
            logger.warning(f"未找到配置文件 {config_path}，当前无工具可用。")
            return

        for server_name, server_info in config.get("mcpServers", {}).items():
            try:
                await self.connect_mcp_server(
                    server_name=server_name,
                    command=server_info["command"],
                    args=server_info["args"],
                    env=server_info.get("env"),
                )
            except Exception as e:
                logger.error(f"服务器 [{server_name}] 启动失败，跳过: {e}", exc_info=True)
                continue

        logger.info(f"工具加载完成，共挂载 {len(self._tool_registry)} 个工具")

    async def connect_mcp_server(
        self,
        server_name: str,
        command: str,
        args: List[str],
        env: Optional[Dict[str, str]] = None,
    ) -> None:
        logger.info(f"正在启动 MCP Server [{server_name}]: {command} {' '.join(args)}")

        resolved_env: Optional[Dict[str, str]] = None
        if env:
            resolved_env = {}
            for k, v in env.items():
                resolved_env[k] = (
                    v.replace("${PROJECT_DIR}", os.getenv("PROJECT_DIR", ""))
                    .replace("${AGENT_WORKSPACE}", os.getenv("AGENT_WORKSPACE", ""))
                )
            logger.info(f"MCP Server [{server_name}] 环境变量: {resolved_env}")

        server_params = StdioServerParameters(command=command, args=args, env=resolved_env)

        try:
            stdio_transport = await self._exit_stack.enter_async_context(stdio_client(server_params))
            read, write = stdio_transport

            session = await self._exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()

            mcp_tools = await session.list_tools()

            for tool in mcp_tools.tools:
                openai_schema = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema,
                    }
                }
                self._tool_registry[tool.name] = {
                    "schema": openai_schema,
                    "session": session,
                }
                logger.info(f"已注册 MCP 工具: {tool.name} (来自 {server_name})")

        except Exception as e:
            logger.error(f"连接 MCP Server [{server_name}] 失败: {str(e)}", exc_info=True)

    def get_schemas(self) -> List[Dict[str, Any]]:
        return [meta["schema"] for meta in self._tool_registry.values()]

    async def call_tool(self, name: str, arguments_json: str) -> str:
        start_time = time.time()

        if name not in self._tool_registry:
            logger.error(f"工具未找到: {name}")
            return f"错误: 工具 '{name}' 未找到。"

        tool_meta = self._tool_registry[name]
        session: ClientSession = tool_meta["session"]
        args: Dict[str, Any] = json.loads(arguments_json) if arguments_json else {}

        logger.info(f"[ToolCall] {name} | 输入: {args}")

        try:
            result = await session.call_tool(name, arguments=args)

            if result.content:
                output = result.content[0].text
                elapsed = time.time() - start_time
                logger.info(f"[ToolCall] {name} | 耗时: {elapsed:.2f}s | 输出: {output}")
                return output
            elapsed = time.time() - start_time
            logger.info(f"[ToolCall] {name} | 耗时: {elapsed:.2f}s | 输出: (空)")
            return "执行成功，无返回值。"

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"[ToolCall] {name} | 耗时: {elapsed:.2f}s | 错误: {str(e)}", exc_info=True)
            return f"执行工具 '{name}' 时出错: {str(e)}"

    async def close(self) -> None:
        await self._exit_stack.aclose()
        logger.info("已断开所有 MCP Server 连接")
