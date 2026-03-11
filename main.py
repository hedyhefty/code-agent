import asyncio
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from src.llm_client import LLMClient

console = Console()


class ChatCLI:
    def __init__(self):
        self.client = LLMClient()
        self.running = True
        self.system_prompt = "你是一个有帮助的AI助手。请用中文回答用户的问题。"

    def print_welcome(self):
        console.print(Panel.fit(
            "[bold cyan]🤖 Code Agent - 持久化版[/bold cyan]\n"
            "[yellow]输入 'quit' 退出 | 'clear' 清空 | 'sessions' 查看历史 | 'load <id>' 加载[/yellow]",
            border_style="cyan"
        ))

    async def handle_chat(self, user_input: str):
        full_text = ""
        console.print("[bold cyan]助手[/bold cyan]")

        # 使用 vertical_overflow="visible" 解决长文本卡顿问题
        with Live(Markdown(""), console=console, refresh_per_second=4, vertical_overflow="visible") as live:
            async for chunk in self.client.chat_stream(user_input, self.system_prompt):
                if chunk:
                    full_text += chunk
                    live.update(Markdown(full_text))
        console.print()

    async def chat_loop(self):
        self.print_welcome()
        while self.running:
            try:
                user_input = Prompt.ask("[bold green]你[/bold green]").strip()
                if not user_input: continue

                # --- 新增：命令路由 ---
                cmd = user_input.lower()
                if cmd in ['quit', 'exit', 'q']:
                    console.print("[yellow]再见！[/yellow]")
                    self.running = False
                elif cmd == 'clear':
                    self.client.history.start_new_session(self.system_prompt)
                    console.print("[green]对话已重置[/green]")
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