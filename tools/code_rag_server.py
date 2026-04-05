import os
from typing import Set

from mcp.server.fastmcp import FastMCP

from rag_service import CodeRagService

mcp = FastMCP("CodeRAG")

rag_service = CodeRagService()

IGNORE_DIRS: Set[str] = {'.git', '.mcp_cache', '__pycache__', 'node_modules', '.venv', 'venv', 'target', 'build'}
IGNORE_EXTS: Set[str] = {'.class', '.jar', '.exe', '.png', '.jpg', '.pdf', '.zip', '.tar', '.gz'}


@mcp.tool()
async def build_code_index(workspace: str) -> str:
    """
    遍历工作区的所有代码文件，构建或重建全局语义搜索向量索引。
    在项目结构发生巨大变化时调用此工具。
    :param workspace: 当前项目的工作区
    """
    try:
        rag_service.clear_index()
        indexed_count = 0

        for root, dirs, files in os.walk(workspace):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in IGNORE_EXTS:
                    continue

                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    rel_path = os.path.relpath(file_path, workspace)
                    rag_service.index_file(rel_path, content)
                    indexed_count += 1
                except UnicodeDecodeError:
                    pass
                except Exception:
                    pass

        return f"✅ 索引构建成功！共扫描并向量化了 {indexed_count} 个代码文件。"
    except Exception as e:
        return f"❌ 索引构建失败: {str(e)}"


@mcp.tool()
async def semantic_search_code(query: str) -> str:
    """
    当不知道某个类、方法或业务逻辑在哪个文件时，
    使用自然语言（如'登录校验逻辑'、'UserService'）进行模糊语义搜索。
    :param query: 查询入参
    """
    try:
        results = rag_service.search(query)
        if not results:
            return "未找到相关的代码片段。"

        output = [f"🔎 语义搜索 '{query}' 的结果:"]
        for i, res in enumerate(results, 1):
            output.append(f"\n--- 结果 {i} | 文件: {res['path']} ---")
            output.append(res['content'])

        return "\n".join(output)
    except Exception as e:
        return f"搜索失败: {str(e)}"


if __name__ == "__main__":
    mcp.run()
