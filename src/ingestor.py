import os
import time
import json
from kafka import KafkaProducer
from langchain_community.document_loaders import PyPDFLoader

UPLOAD_FOLDER = "/app/uploads"

def start_ingestor_service():
    print("📂 Ingestor Service Started...")
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    processed_files = set()

    while True:
        # 简单轮询：检查新文件
        files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(".pdf")]
        for f in files:
            if f not in processed_files:
                filepath = os.path.join(UPLOAD_FOLDER, f)
                print(f"📄 Found new file: {f}")

                # 1. 加载 PDF
                loader = PyPDFLoader(filepath)
                pages = loader.load_and_split()

                # 2. 发送 Kafka
                for page in pages:
                    payload = {
                        "text": page.page_content,
                        "metadata": {"source": f, "page": page.metadata.get("page", 0)}
                    }
                    producer.send("doc_chunks", payload)

                producer.flush()
                processed_files.add(f)
                print(f"🚀 Sent {len(pages)} chunks to Kafka")

        time.sleep(5)
