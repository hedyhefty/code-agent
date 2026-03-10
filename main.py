import asyncio

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from src.llm_client import LLMClient

console = Console()


class ChatCLI:
    def __init__(self):
        self.client = LLMClient()
        self.running = True
        self.system_prompt = "你是一个有帮助的AI助手。请用中文回答用户的问题。"

    def print_welcome(self):
        console.print(Panel.fit(
            "[bold cyan]🤖 Code Agent - 优化版[/bold cyan]\n"
            "[yellow]输入 'quit' 退出 | 'clear' 清空对话[/yellow]",
            border_style="cyan"
        ))

    async def handle_chat(self, user_input: str):
        full_text = ""
        console.print("[bold cyan]助手[/bold cyan]")  # 标签单独占一行，避免对齐问题

        with Live(Markdown(""), console=console, refresh_per_second=12, vertical_overflow="visible") as live:
            async for chunk in self.client.chat_stream(user_input, self.system_prompt):
                if chunk:
                    full_text += chunk
                    # 实时将字符串解析为 Markdown 对象
                    live.update(Markdown(full_text))

    async def chat_loop(self):
        self.print_welcome()

        while self.running:
            try:
                user_input = Prompt.ask("[bold green]你[/bold green]").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'q']:
                    console.print("[yellow]再见！[/yellow]")
                    self.running = False
                elif user_input.lower() == 'clear':
                    self.client.clear_messages()
                    console.print("[green]对话历史已清空[/green]")
                else:
                    await self.handle_chat(user_input)

            except KeyboardInterrupt:
                console.print("\n[yellow]程序已中断[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]运行错误: {e}[/red]")


async def main():
    cli = ChatCLI()
    await cli.chat_loop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
