import logging
import os
import sys
from typing import Any, Dict, List, Optional

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from langchain_core.documents import Document

os.environ["TQDM_DISABLE"] = "True"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
logger = logging.getLogger("CodeAgent.RAG")
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class CodeRagService:
    def __init__(self) -> None:
        self.embedding_model_path: Optional[str] = os.environ.get("EMBEDDING_MODEL_PATH")
        self.db_path: Optional[str] = os.environ.get("RAG_DB_PATH")

        if not self.embedding_model_path:
            raise ValueError("环境变量 EMBEDDING_MODEL_PATH 未设置")
        if not self.db_path:
            raise ValueError("环境变量 RAG_DB_PATH 未设置")

        os.makedirs(self.db_path, exist_ok=True)
        self.embeddings: Optional[HuggingFaceEmbeddings] = None
        self.vector_store: Optional[Chroma] = None
        self._init()

    def _init(self) -> None:
        self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_model_path)
        self.vector_store = Chroma(
            collection_name="codebase_index",
            embedding_function=self.embeddings,
            persist_directory=self.db_path,
        )

    def index_file(self, file_path: str, content: str) -> None:
        ext = file_path.split('.')[-1].lower()

        lang_map: Dict[str, Language] = {
            'java': Language.JAVA,
            'py': Language.PYTHON,
            'js': Language.JS,
            'ts': Language.TS,
            'cpp': Language.CPP,
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

    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        results = self.vector_store.similarity_search(query, k=k)
        return [{"path": doc.metadata.get("path"), "content": doc.page_content} for doc in results]

    def clear_index(self) -> None:
        self.vector_store.delete_collection()
        self.vector_store = Chroma(
            collection_name="codebase_index",
            embedding_function=self.embeddings,
            persist_directory=self.db_path,
        )
