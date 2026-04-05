import logging
import os
import tempfile
from typing import List, Optional

import docker
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("CodeExecutor")

mcp = FastMCP("CodeExecutorServer")
try:
    docker_client = docker.from_env()
except docker.errors.DockerException:
    logger.warning("无法连接到 Docker 守护进程。请确保 Docker 已启动。")
    docker_client = None


def _cleanup_leaked_containers() -> None:
    """检测并清理异常退出的容器（每次执行前调用）"""
    if not docker_client:
        return
    try:
        containers = docker_client.containers.list(all=True)
        for c in containers:
            if c.status != "running" and c.name and c.name.startswith("python:"):
                logger.warning(f"发现泄漏容器 {c.name}，正在清理")
                c.remove(force=True)
    except Exception:
        pass


@mcp.tool()
def execute_python_code(code: str, timeout_seconds: int = 10) -> str:
    """
    在一个安全的 Docker 沙盒环境中执行 Python 代码并返回输出结果。
    注意：此工具不挂载任何工作区目录。如果你需要运行项目内的代码（涉及 import 或多文件），请务必使用 run_script_file。

    :param code: 需要执行的完整 Python 代码字符串。
    :param timeout_seconds: 执行超时时间（秒），默认 10 秒。
    """
    if not docker_client:
        return "执行失败: 宿主机未连接到 Docker 守护进程。"

    _cleanup_leaked_containers()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name

    container = None
    try:
        container = docker_client.containers.run(
            image="python:3.10-alpine",
            command="python /app/script.py",
            volumes={temp_file_path: {'bind': '/app/script.py', 'mode': 'ro'}},
            working_dir="/app",
            detach=True,
            mem_limit="128m",
            network_disabled=True,
        )

        result = container.wait(timeout=timeout_seconds)
        logs = container.logs().decode('utf-8')

        exit_code = result.get('StatusCode', -1)
        if exit_code == 0:
            return f"✅ 执行成功:\n{logs}"
        else:
            return f"❌ 执行报错 (退出码 {exit_code}):\n{logs}"

    except docker.errors.ContainerError as e:
        return f"❌ 容器运行错误:\n{e.stderr.decode('utf-8') if e.stderr else str(e)}"
    except Exception as e:
        return f"⚠️ 执行中断: {str(e)}"
    finally:
        if container:
            try:
                container.remove(force=True)
            except Exception:
                pass
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@mcp.tool()
def run_script_file(host_workspace: str, file_path: str, args: Optional[List[str]] = None) -> str:
    """
    在隔离的容器中执行工作区内的 Python 脚本。
    注意：此工具会自动处理宿主机到容器的路径映射。

    :param host_workspace: 工作空间的路径
    :param file_path: 脚本相对于工作区的路径 (例如: 'project/hello.py')
    :param args: 命令行参数列表 (例如: ['--verbose', '10'])
    """
    container_workspace = "/app/workspace"
    safe_file_path = os.path.normpath(file_path).lstrip("/")
    full_container_path = os.path.join(container_workspace, safe_file_path)

    command: List[str] = ["python3", full_container_path]
    if args:
        command.extend(args)

    try:
        output = docker_client.containers.run(
            image="python:3.10-slim",
            command=command,
            volumes={host_workspace: {'bind': container_workspace, 'mode': 'rw'}},
            working_dir=container_workspace,
            detach=False,
            remove=True,
        )
        return f"✅ 执行成功:\n{output.decode('utf-8')}"

    except docker.errors.ContainerError as e:
        return f"❌ 执行报错 (返回码 {e.exit_status}):\n{e.stderr.decode('utf-8')}"
    except Exception as e:
        return f"❌ 系统异常: {str(e)}"


if __name__ == "__main__":
    if docker_client:
        try:
            docker_client.images.get("python:3.10-alpine")
        except docker.errors.ImageNotFound:
            docker_client.images.pull("python:3.10-alpine")

    mcp.run()
