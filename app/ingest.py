# app/ingest.py

from app.utils import get_consumer
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

import time

embeddings = OpenAIEmbeddings()
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)

def consume_and_index():
    consumer = get_consumer()
    print("Kafka consumer started...")
    for message in consumer:
        data = message.value
        doc_id = data["doc_id"]
        content = data["content"]
        print(f"Processing doc: {doc_id}")

        # 文本切分
        chunks = text_splitter.split_text(content)

        # 元数据附加doc_id
        metadatas = [{"doc_id": doc_id}] * len(chunks)

        # 向量数据库添加
        vectorstore.add_texts(chunks, metadatas)
        vectorstore.persist()
        print(f"Doc {doc_id} indexed with {len(chunks)} chunks")

        time.sleep(0.5)  # 控制消费节奏

if __name__ == "__main__":
    consume_and_index()
