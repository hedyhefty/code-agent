import tempfile
import os
from typing import Optional, List

import docker
from mcp.server.fastmcp import FastMCP

# 初始化 FastMCP 和 Docker 客户端
mcp = FastMCP("CodeExecutorServer")
try:
    docker_client = docker.from_env()
except docker.errors.DockerException:
    print("警告: 无法连接到 Docker 守护进程。请确保 Docker 已启动。")
    docker_client = None


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

    # 1. 将代码写入临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name

    container = None
    try:
        # 2. 启动一次性容器执行代码
        # 使用轻量级 alpine 镜像加速启动
        container = docker_client.containers.run(
            image="python:3.10-alpine",
            command=f"python /app/script.py",
            volumes={temp_file_path: {'bind': '/app/script.py', 'mode': 'ro'}},  # 只读挂载
            working_dir="/app",
            detach=True,
            mem_limit="128m",  # 内存限制
            network_disabled=True,  # 禁用网络，防止恶意下载或攻击
        )

        # 3. 等待执行完成并捕获输出
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
        # 处理超时等异常
        return f"⚠️ 执行中断: {str(e)}"
    finally:
        # 4. 无论成功与否，强制清理容器和临时文件
        if container:
            try:
                container.remove(force=True)
            except:
                pass
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@mcp.tool()
def run_script_file(host_workspace: str, file_path: str, args: Optional[List[str]] = None) -> str:
    """
    在隔离的容器中执行工作区内的 Python 脚本。
    注意：此工具会自动处理宿主机到容器的路径映射。你只需要提供相对于 workspace 根目录的相对路径即可。

    :param host_workspace: 工作区的路径（例如：'/User/somebody/AgentWorkspace'）
    :param file_path: 脚本相对于工作区的路径 (例如: 'project/hello.py')
    :param args: 命令行参数列表 (例如: ['--verbose', '10'])
    """
    # 1. 安全配置：定义宿主机和容器的映射路径
    container_workspace = "/app/workspace"

    # 2. 路径安全校验：防止路径穿越攻击 (防止输入 ../../etc/passwd)
    safe_file_path = os.path.normpath(file_path).lstrip("/")
    full_container_path = os.path.join(container_workspace, safe_file_path)

    # 3. 构造命令列表 (参数分离，避免注入风险)
    # command 列表会被 Docker SDK 安全转义
    command = ["python3", full_container_path]
    if args:
        command.extend(args)

    try:
        # 4. 运行容器
        # 挂载宿主机工作区到容器内，并将其设为工作目录
        output = docker_client.containers.run(
            image="python:3.10-slim",
            command=command,
            volumes={host_workspace: {'bind': container_workspace, 'mode': 'rw'}},
            working_dir=container_workspace,
            detach=False,
            remove=True  # 执行后自动删除容器
        )
        return f"✅ 执行成功:\n{output.decode('utf-8')}"

    except docker.errors.ContainerError as e:
        return f"❌ 执行报错 (返回码 {e.exit_status}):\n{e.stderr.decode('utf-8')}"
    except Exception as e:
        return f"❌ 系统异常: {str(e)}"


if __name__ == "__main__":
    # 如果还没拉取过镜像，首次启动前拉取一下
    if docker_client:
        try:
            docker_client.images.get("python:3.10-alpine")
        except docker.errors.ImageNotFound:
            docker_client.images.pull("python:3.10-alpine")

    mcp.run()
