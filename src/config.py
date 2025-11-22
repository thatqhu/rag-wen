import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件（如果容器启动时没有注入 env，这里作为一个 fallback）
load_dotenv()

class Settings:
    # --- 基础路径配置 ---
    # 定位到项目根目录 /app
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    # 上传文件存储目录
    UPLOAD_DIR = BASE_DIR / "uploads"

    # --- Kafka 配置 ---
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    KAFKA_TOPIC_DOCS = "doc_chunks"
    KAFKA_GROUP_ID = "rag_group"

    # --- Chroma 向量库配置 ---
    CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "/chroma_data")
    CHROMA_COLLECTION_NAME = "rag_collection"

    # --- LLM 模型配置 ---
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    # 如果用的是 OpenAI，推荐 gpt-4o-mini 或 gpt-3.5-turbo 性价比高
    LLM_MODEL_NAME = "gpt-4o-mini"
    EMBEDDING_MODEL = "text-embedding-3-small"

    # --- 检索配置 ---
    RETRIEVER_K = 4  # 每次检索召回多少个片段

    def init_dirs(self):
        """初始化必要的目录"""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.init_dirs()
