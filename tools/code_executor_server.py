import tempfile
import os
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


if __name__ == "__main__":
    # 如果还没拉取过镜像，首次启动前拉取一下
    if docker_client:
        try:
            docker_client.images.get("python:3.10-alpine")
        except docker.errors.ImageNotFound:
            docker_client.images.pull("python:3.10-alpine")

    mcp.run()