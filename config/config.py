import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Kafka配置
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    KAFKA_TOPIC_DOCUMENTS = 'documents'
    KAFKA_TOPIC_QUERIES = 'queries'
    KAFKA_GROUP_ID = 'rag-consumer-group'

    # Chroma配置
    CHROMA_HOST = os.getenv('CHROMA_HOST', 'localhost')
    CHROMA_PORT = int(os.getenv('CHROMA_PORT', 8000))
    CHROMA_COLLECTION = 'documents_collection'

    # LLM配置
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
    LLM_MODEL = 'gpt-3.5-turbo'

    # RAG配置
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    RETRIEVAL_K = 4
