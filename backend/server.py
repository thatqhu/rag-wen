import json
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from agent import graph # 导入新的 graph

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

async def sse_generator(user_message: str):
    inputs = {
        "messages": [HumanMessage(content=user_message)],
        "revision_count": 0
    }

    # 监听所有 v1 版本事件
    async for event in graph.astream_events(inputs, version="v1"):
        kind = event["event"]
        name = event["name"]

        # 1. 捕获 LLM 生成的文本 (Streaming)
        # 我们只关心 'agent' 节点产生的文本，不关心 'reflect' 产生的批评意见
        if kind == "on_chat_model_stream" and "agent" in event.get("tags", []):
             # 注意：如果 Agent 正在生成 Tool Call 参数，chunk.content 是空的，这里会自动忽略
            chunk = event["data"].get("chunk")
            if chunk and hasattr(chunk, "content"):
                content = chunk.content
                if content:
                    payload = json.dumps({"type": "token", "content": content})
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"

        # 2. 捕获状态变化 (用于前端 UI 展示)
        elif kind == "on_chain_start":
            if name == "tools":
                yield f"data: {json.dumps({'type': 'status', 'content': '🔍 正在搜索网络...'})}\n\n"
            elif name == "reflect":
                yield f"data: {json.dumps({'type': 'status', 'content': '🤔 正在审查答案质量...'})}\n\n"
            elif name == "agent":
                # 区分是第一次思考还是重写
                yield f"data: {json.dumps({'type': 'status', 'content': '✍️ 正在撰写/修改回复...'})}\n\n"

    yield "data: [DONE]\n\n"

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    return StreamingResponse(sse_generator(req.message), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
