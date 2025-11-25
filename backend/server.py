import json, os
import uuid
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from worker_kafka import consume

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
TOPIC_REQUEST = 'rag_requests'

producer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global producer
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    print("Server Producer started.")
    yield
    await producer.stop()
    print("Server Producer stopped.")

app = FastAPI(lifespan=lifespan)

class ChatRequest(BaseModel):
    message: str
    thread_id: str = None

async def kafka_stream_generator(target_thread_id: str):
    """
    这是一个异步生成器，它会创建一个临时的 Kafka Consumer，
    专门监听指定 thread_id 的消息。
    """
    consumer = AIOKafkaConsumer(
        'rag_responses', # 监听结果主题
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=f"web-client-{target_thread_id}", # 确保每个请求有独立的 Consumer Group (或者用随机UUID)
        auto_offset_reset='latest' # 只听最新的
    )
    await consumer.start()

    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode('utf-8'))

            # 关键过滤：只处理当前用户的消息
            if data.get('thread_id') == target_thread_id:

                # 格式化为 SSE (Server-Sent Events) 标准格式
                # 格式: "data: {JSON payload}\n\n"
                yield f"data: {json.dumps(data)}\n\n"

                # 结束条件：如果收到完成信号或错误
                if data.get('type') in ['result', 'error']:
                    break
    finally:
        await consumer.stop()

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    thread_id = req.thread_id or str(uuid.uuid4())

    payload = {
        "thread_id": thread_id,
        "message": req.message,
        "timestamp": asyncio.get_event_loop().time()
    }

    try:
        await producer.send_and_wait(
            TOPIC_REQUEST,
            json.dumps(payload).encode('utf-8')
        )
        # 3. 立即返回流式响应 (Consumer)
        # 这里的 generator 会在后台持续运行，直到任务结束
        return StreamingResponse(
            kafka_stream_generator(thread_id),
            media_type="text/event-stream"
        )
    except Exception as e:
        return {"status": "error", "detail": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
