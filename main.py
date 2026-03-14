import asyncio
import logging
from platform import libc_ver

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from src.llm_client import LLMClient
from src.logger import setup_logging

# 初始化日志系统
setup_logging()
logger = logging.getLogger("CodeAgent.main")
logger.info("Code Agent 主程序启动")

console = Console()


class ChatCLI:
    def __init__(self):
        self.client = LLMClient()

        self.running = True
        self.system_prompt = "你是一个有帮助的AI助手。请用中文回答用户的问题。"

    def print_welcome(self):
        console.print(Panel.fit(
            "[bold cyan]🤖 Code Agent - 持久化版[/bold cyan]\n"
            "[yellow]输入 'quit' 退出 | 'new' 开启新会话 | 'sessions' 查看历史 | 'load <id>' 加载[/yellow]",
            border_style="cyan"
        ))

    def print_loaded_tools(self):
        tools = self.client.tool_manager.get_schemas()
        if not tools:
            console.print("[red]警告：没有加载到任何工具！请检查 tools/ 目录是否存在以及 __init__.py 是否就位。[/red]")
        else:
            console.print(f"[green]成功加载 {len(tools)} 个工具：{[t['function']['name'] for t in tools]}[/green]")

    async def handle_chat(self, user_input: str):
        full_text = "🤔 思考中..."  # 初始值
        console.print("[bold cyan]助手[/bold cyan]")

        # 使用 vertical_overflow="visible" 解决长文本卡顿问题
        with Live(Markdown(""), console=console, refresh_per_second=4, vertical_overflow="visible") as live:
            live.update(Markdown(full_text))
            async for chunk in self.client.chat_stream(user_input, self.system_prompt):
                # --- 新增：拦截擦除暗号 ---
                if chunk == "<CLEAR_THINKING>":
                    full_text = full_text.replace("🤔 思考中...", "")
                    live.update(Markdown(full_text))
                    continue  # 跳过这一轮，不要把暗号加到 full_text 里

                if chunk:
                    full_text += chunk
                    live.update(Markdown(full_text))
        console.print()

    async def chat_loop(self):
        self.print_welcome()
        self.print_loaded_tools()

        while self.running:
            try:
                user_input = Prompt.ask("[bold green]你[/bold green]").strip()
                if not user_input: continue

                # --- 新增：命令路由 ---
                cmd = user_input.lower()
                if cmd in ['quit', 'exit', 'q']:
                    console.print("[yellow]再见！[/yellow]")
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
                    # --- 普通对话 ---
                    await self.handle_chat(user_input)

            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]运行错误: {e}[/red]")


async def main():
    cli = ChatCLI()
    await cli.chat_loop()


if __name__ == "__main__":
    asyncio.run(main())
