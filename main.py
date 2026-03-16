import asyncio
import logging
import os

from dotenv import load_dotenv
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from src.llm_client import LLMClient
from src.logger import setup_logging

load_dotenv()

setup_logging()
logger = logging.getLogger("CodeAgent.main")
logger.info("Code Agent 主程序启动")

console = Console()


class ChatCLI:
    def __init__(self):
        self.client = LLMClient()
        self.running = True
        self.workspace = os.getcwd()
        self.system_prompt = f"""
        你是一个顶级的软件工程师和架构师，现在作为 CLI 环境下的智能编程助手（Code Agent）运行。
        你的核心目标是通过逻辑严密的分析和使用提供的工具，独立完成或协助用户完成代码编写、重构、Bug修复和测试验证任务。
        请始终用专业、简洁的中文与用户沟通。

        【运行环境与空间拓扑】
        你具备强大的工具链，但请务必认清工具运行的物理边界：
        1. 文件系统：你的文件操作工具（如 write_file, read_directory）工作在宿主机受控的工作区内，项目的工作区为：{self.workspace}
        2. 代码执行沙箱：你的代码执行工具（如 run_script_file）运行在隔离的 Linux Docker 容器中。
        3. ⚠️ 核心映射关系：宿主机的工作区目录已经被无缝挂载到容器内的 `/app/workspace`。这意味着你在宿主机写入的本地模块，可以直接在容器的该路径下被 `import` 和执行。

        【工具使用规范】
        1. 职责分离：编写和修改文件请使用文件系统工具；执行完整的脚本请使用 `run_script_file`。
        2. 参数传递：调用 `run_script_file` 运行带参数的脚本时，务必将命令行参数拆分并放入独立的 `args` 数组中，绝不可将参数硬拼接到 file_path 字符串内。
        3. 路径基准：执行脚本时，Python 解释器的默认工作目录（working_dir）即为 `/app/workspace`，请注意相对路径的使用。

        【ReAct 工作流与行为准则】
        1. 谋定后动：面对复杂任务时，先进行思考（Thinking），拆解步骤。不要试图在一个工具调用里做完所有事。
        2. 闭环验证：如果你修改了代码，请主动寻找或编写对应的测试代码，调用执行工具来验证你的修改是否真正生效。
        3. 错误自愈：如果工具返回了报错信息（如 traceback 或权限拒绝），不要立刻向用户求助。仔细阅读报错，分析原因，尝试自我修复并重新执行。
        """

    def print_welcome(self):
        welcome_text = f"""
        [bold cyan]🤖 Code Agent - MCP 架构演进版[/bold cyan]
        [yellow]输入 'quit' 退出 | 'new' 开启新会话 | 'sessions' 查看历史 | 'load <id>' 加载[/yellow]
        工作空间：{self.workspace},
        """
        console.print(Panel.fit(
            welcome_text,
            border_style="cyan"
        ))

    def print_loaded_tools(self):
        tools = self.client.mcp_client.get_schemas()
        if not tools:
            console.print("[red]警告：没有加载到任何工具！请检查 mcp_config.json 配置。[/red]")
        else:
            console.print(
                f"[green]成功通过 MCP 挂载 {len(tools)} 个工具：{[t['function']['name'] for t in tools]}[/green]")

    async def handle_chat(self, user_input: str):
        full_text = "🤔 思考中..."
        console.print("[bold cyan]助手[/bold cyan]")

        with Live(Markdown(""), console=console, refresh_per_second=4, vertical_overflow="visible") as live:
            live.update(Markdown(full_text))
            async for chunk in self.client.chat_stream(user_input, self.system_prompt):
                if chunk == "<CLEAR_THINKING>":
                    full_text = full_text.replace("🤔 思考中...", "")
                    live.update(Markdown(full_text))
                    continue

                if chunk:
                    full_text += chunk
                    live.update(Markdown(full_text))
        console.print()

    async def chat_loop(self):
        self.print_welcome()

        # --- 核心改动：在进入循环前启动所有的 MCP Server ---
        await self.client.startup()
        self.print_loaded_tools()

        try:
            while self.running:
                user_input = Prompt.ask("[bold green]你[/bold green]").strip()
                if not user_input: continue

                cmd = user_input.lower()
                if cmd in ['quit', 'exit', 'q']:
                    console.print("[yellow]再见！正在清理资源...[/yellow]")
                    self.running = False
                elif cmd == 'new':
                    self.client.history.start_new_session(self.system_prompt)
                    console.print("[green]已开启新会话[/green]")
                elif cmd == 'sessions':
                    sessions = self.client.history.list_sessions()
                    console.print(f"[blue]历史会话: {sessions}[/blue]")
                elif cmd.startswith('load '):
                    sid = user_input.split(" ")[1]
                    if self.client.history.load_session(sid):
                        console.print(f"[green]已加载会话: {sid}[/green]")
                    else:
                        console.print("[red]会话不存在[/red]")
                else:
                    await self.handle_chat(user_input)
        except KeyboardInterrupt:
            console.print("\n[yellow]强制退出，正在清理资源...[/yellow]")
        finally:
            # --- 核心改动：确保程序退出时杀掉所有的外部 Server 进程 ---
            await self.client.mcp_client.close()


async def main():
    cli = ChatCLI()
    await cli.chat_loop()


if __name__ == "__main__":
    asyncio.run(main())
