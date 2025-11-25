import json,os
import asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from langchain_core.messages import HumanMessage, AIMessage
from agent import graph

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
TOPIC_REQUEST = 'rag_requests'
TOPIC_RESPONSE = 'rag_responses'

async def handle_node_status(event: dict):
    name = event["name"]
    status_map = {
        "tools": "Searching web...",
        "reflect": "Critiquing response...",
        "agent": "Generating answer..."
    }
    if name in status_map:
        return {"type": "status", "content": status_map[name]}
    return None

async def handle_final_result(event: dict, graph_config: dict):
    name = event["name"]
    if name != "reflect":
        return None

    output = event["data"].get("output")
    if not output or "messages" not in output:
        return None

    last_msg = output["messages"][-1]

    if "APPROVE" not in last_msg.content:
        return None

    final_state = graph.get_state(graph_config)
    for msg in reversed(final_state.values["messages"]):
        if isinstance(msg, AIMessage) and msg.content and "APPROVE" not in msg.content:
            return {"type": "result", "content": msg.content}
    return None

async def process_message(msg, producer):
    try:
        data = json.loads(msg.value.decode('utf-8'))
        thread_id = data.get('thread_id')
        user_message = data.get('message')

        print(f"Processing request for thread: {thread_id}")

        config = {"configurable": {"thread_id": thread_id}}
        inputs = {
            "messages": [HumanMessage(content=user_message)],
            "revision_count": 0
        }

        async for event in graph.astream_events(inputs, config=config, version="v1"):
            kind = event["event"]
            payload = None

            if kind == "on_chain_start":
                payload = await handle_node_status(event)
            elif kind == "on_chain_end":
                payload = await handle_final_result(event, config)

            if payload:
                payload['thread_id'] = thread_id
                await producer.send_and_wait(
                    TOPIC_RESPONSE,
                    json.dumps(payload).encode('utf-8')
                )
                print(f"Sent update: {payload['type']}")

    except Exception as e:
        print(f"Error processing message: {e}")
        error_payload = {"thread_id": thread_id, "type": "error", "content": str(e)}
        await producer.send_and_wait(TOPIC_RESPONSE, json.dumps(error_payload).encode('utf-8'))

async def consume():
    consumer = AIOKafkaConsumer(
        TOPIC_REQUEST,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="rag_agent_group"
    )
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS
    )

    await consumer.start()
    await producer.start()
    print("Agent worker started. Listening for tasks...")

    try:
        async for msg in consumer:
            # 这里可以优化为 asyncio.create_task 来并行处理多个请求
            # 但要注意 SQLite (MemorySaver) 的并发写入锁问题
            await process_message(msg, producer)
    finally:
        await consumer.stop()
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(consume())
