from kafka import KafkaConsumer
import json
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import chromadb
from config.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentConsumer:
    """消费Kafka文档消息并处理成向量存储"""

    def __init__(self):
        # 初始化Kafka消费者
        self.consumer = KafkaConsumer(
            Config.KAFKA_TOPIC_DOCUMENTS,
            bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
            group_id=Config.KAFKA_GROUP_ID,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )

        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            length_function=len
        )

        # 初始化嵌入模型
        self.embeddings = HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL
        )

        # 连接Chroma
        self.chroma_client = chromadb.HttpClient(
            host=Config.CHROMA_HOST,
            port=Config.CHROMA_PORT
        )

        # 初始化向量存储
        self.vector_store = Chroma(
            client=self.chroma_client,
            collection_name=Config.CHROMA_COLLECTION,
            embedding_function=self.embeddings
        )

        logger.info("Document Consumer初始化完成")

    def process_document(self, message):
        """
        处理单个文档消息：分块、向量化、存储

        Args:
            message: Kafka消息，包含doc_id, content, metadata
        """
        try:
            doc_id = message['doc_id']
            content = message['content']
            metadata = message.get('metadata', {})

            logger.info(f"开始处理文档: {doc_id}")

            # 1. 文本分块
            chunks = self.text_splitter.create_documents(
                texts=[content],
                metadatas=[{**metadata, 'doc_id': doc_id}]
            )

            logger.info(f"文档 {doc_id} 分割成 {len(chunks)} 个块")

            # 2. 向量化并存储到Chroma
            self.vector_store.add_documents(chunks)

            logger.info(f"文档 {doc_id} 成功存储到向量数据库")

        except Exception as e:
            logger.error(f"处理文档失败: {e}")

    def start_consuming(self):
        """开始消费Kafka消息"""
        logger.info("开始监听Kafka消息...")

        try:
            for message in self.consumer:
                self.process_document(message.value)
        except KeyboardInterrupt:
            logger.info("停止消费")
        finally:
            self.consumer.close()

# 运行消费者
if __name__ == "__main__":
    consumer = DocumentConsumer()
    consumer.start_consuming()
