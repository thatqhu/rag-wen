import json
import os
from kafka import KafkaConsumer
from core.db import get_vector_store

def start_worker_service():
    print("👷 Worker Service Started...")
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

    # 循环尝试连接 Kafka，直到成功
    consumer = None
    while not consumer:
        try:
            consumer = KafkaConsumer(
                "doc_chunks",
                bootstrap_servers=bootstrap_servers,
                group_id="rag_group",
                value_deserializer=lambda m: json.loads(m.decode("utf-8"))
            )
        except Exception:
            print("Waiting for Kafka...")
            import time; time.sleep(3)

    vector_store = get_vector_store()

    print("✅ Worker connected to Kafka, listening...")
    for msg in consumer:
        data = msg.value
        print(f"📥 Processing chunk: {data.get('source')}")

        # 写入 Chroma
        vector_store.add_texts(
            texts=[data["text"]],
            metadatas=[data["metadata"]]
        )
