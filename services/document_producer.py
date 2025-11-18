from kafka import KafkaProducer
import json
import logging
from config.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProducer:
    """负责将文档发送到Kafka主题"""

    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',
            retries=3
        )
        logger.info(f"Kafka Producer连接成功: {Config.KAFKA_BOOTSTRAP_SERVERS}")

    def send_document(self, doc_id: str, content: str, metadata: dict = None):
        """
        发送文档到Kafka

        Args:
            doc_id: 文档唯一标识
            content: 文档内容
            metadata: 文档元数据（来源、时间戳等）
        """
        message = {
            'doc_id': doc_id,
            'content': content,
            'metadata': metadata or {}
        }

        try:
            future = self.producer.send(Config.KAFKA_TOPIC_DOCUMENTS, value=message)
            result = future.get(timeout=10)
            logger.info(f"文档 {doc_id} 发送成功到分区 {result.partition}")
            return True
        except Exception as e:
            logger.error(f"发送文档失败: {e}")
            return False

    def close(self):
        self.producer.flush()
        self.producer.close()

# 使用示例
if __name__ == "__main__":
    producer = DocumentProducer()

    # 模拟发送多个文档
    documents = [
        {
            'doc_id': 'doc_001',
            'content': '人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统...',
            'metadata': {'source': 'wiki', 'category': 'AI'}
        },
        {
            'doc_id': 'doc_002',
            'content': 'RAG（检索增强生成）是一种结合信息检索和文本生成的技术，通过从知识库检索相关信息来增强LLM的回答质量...',
            'metadata': {'source': 'tech_blog', 'category': 'RAG'}
        }
    ]

    for doc in documents:
        producer.send_document(**doc)

    producer.close()
