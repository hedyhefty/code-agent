import asyncio
import os
import logging
import sys

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# 必须在 import langchain 或 sentence_transformers 之前
os.environ["TQDM_DISABLE"] = "True"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
logger = logging.getLogger("CodeAgent.RAG")
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class CodeRagService:
    def __init__(self):
        # 从环境变量读取路径配置
        self.embedding_model_path = os.environ.get("EMBEDDING_MODEL_PATH")
        self.db_path = os.environ.get("RAG_DB_PATH")

        # 参数校验
        if not self.embedding_model_path:
            raise ValueError("环境变量 EMBEDDING_MODEL_PATH 未设置")
        if not self.db_path:
            raise ValueError("环境变量 RAG_DB_PATH 未设置")

        os.makedirs(self.db_path, exist_ok=True)
        self.embeddings = None
        self._init()

    def _init(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_model_path)
        self.vector_store = Chroma(
            collection_name="codebase_index",
            embedding_function=self.embeddings,
            persist_directory=self.db_path
        )

    def index_file(self, file_path: str, content: str):
        """对单个代码文件进行语法感知切片并存入数据库"""
        ext = file_path.split('.')[-1].lower()

        lang_map = {
            'java': Language.JAVA, 'py': Language.PYTHON,
            'js': Language.JS, 'ts': Language.TS, 'cpp': Language.CPP
        }

        if ext in lang_map:
            splitter = RecursiveCharacterTextSplitter.from_language(
                language=lang_map[ext], chunk_size=1000, chunk_overlap=150
            )
        else:
            splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)

        texts = splitter.split_text(content)
        docs = [
            Document(page_content=t, metadata={"path": file_path})
            for t in texts
        ]
        if docs:
            self.vector_store.add_documents(docs)

    def search(self, query: str, k: int = 3):
        """语义搜索"""
        results = self.vector_store.similarity_search(query, k=k)
        return [{"path": doc.metadata.get("path"), "content": doc.page_content} for doc in results]

    def clear_index(self):
        """清空现有索引（重建时使用）"""
        self.vector_store.delete_collection()
        # 重新初始化空的 collection
        self.vector_store = Chroma(
            collection_name="codebase_index",
            embedding_function=self.embeddings,
            persist_directory=self.db_path
        )
