from mcp.server.fastmcp import FastMCP
from datetime import datetime
import time

# 初始化 FastMCP 实例
mcp = FastMCP("TimeToolsServer")

@mcp.tool()
def get_current_time(time_format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    获取当前系统时间。
    :param time_format: 时间格式字符串，默认为年-月-日 时:分:秒
    """
    return datetime.now().strftime(time_format)

@mcp.tool()
def get_timezone() -> str:
    """获取系统当前设置的时区名称"""
    return time.tzname[0]

if __name__ == "__main__":
    # 启动 MCP 服务器（stdio 模式）
    mcp.run()