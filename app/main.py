# app/main.py

from fastapi import FastAPI
from pydantic import BaseModel
from app.rag_chain import build_rag_chain

class QueryRequest(BaseModel):
    query: str

app = FastAPI()
qa_chain = build_rag_chain()

@app.post("/rag_query/")
async def rag_query(request: QueryRequest):
    result = qa_chain({"query": request.query})
    return {
        "answer": result["result"],
        "sources": [
            {
                "metadata": doc.metadata,
                "preview": doc.page_content[:200]
            }
            for doc in result.get("source_documents", [])
        ]
    }
