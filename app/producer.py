# app/producer.py

from app.utils import get_producer
import time

producer = get_producer()

def send_doc(doc_id: str, content: str):
    message = {"doc_id": doc_id, "content": content}
    producer.send('doc_ingest_topic', value=message)
    producer.flush()
    print(f"Sent doc: {doc_id}")

if __name__ == "__main__":
    # 模拟多个文档上传
    docs = {
        "doc1": "Python是一种高级编程语言，广泛用于数据科学、机器学习等。",
        "doc2": "Kafka是一种分布式流处理平台，适合高吞吐量数据。",
        "doc3": "Chroma是开源的向量数据库，专为AI向量检索设计。"
    }
    for doc_id, content in docs.items():
        send_doc(doc_id, content)
        time.sleep(1)  # 模拟间隔
