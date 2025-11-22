from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from .config import settings

def get_vector_store():
    """获取 Chroma 向量库实例"""
    return Chroma(
        collection_name=settings.CHROMA_COLLECTION_NAME,
        embedding_function=OpenAIEmbeddings(model=settings.EMBEDDING_MODEL),
        persist_directory=settings.CHROMA_DB_DIR
    )
