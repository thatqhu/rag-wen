import json
import uuid
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from agent import graph

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

def format_sse(event_type: str, content: str) -> str:
    payload = json.dumps({"type": event_type, "content": content})
    return f"data: {payload}\n\n"

async def handle_node_status(event: dict):
    name = event["name"]
    status_map = {
        "tools": "Searching...",
        "reflect": "Reviewing...",
        "agent": "Thinking..."
    }

    if name in status_map:
        return format_sse("status", status_map[name])
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

    # the tricky thing is we only return the final approved message, but not the ai result message
    # let's go back to state get the real result
    final_state = graph.get_state(graph_config) # type: ignore
    for msg in reversed(final_state.values["messages"]):
        if isinstance(msg, AIMessage) and msg.content and "APPROVE" not in msg.content:
             return format_sse("result", msg.content) # type: ignore

    return None

async def sse_generator(user_message: str):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    inputs = {
        "messages": [HumanMessage(content=user_message)],
        "revision_count": 0
    }

    async for event in graph.astream_events(inputs, config=config, version="v1"): # type: ignore
        kind = event["event"]

        result = None

        if kind == "on_chain_start":
            result = await handle_node_status(event) # type: ignore

        elif kind == "on_chain_end":
            result = await handle_final_result(event, config) # type: ignore

        if result:
            yield result

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    return StreamingResponse(sse_generator(req.message), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
