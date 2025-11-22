import shutil
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from core.rag import get_rag_chain
from core.config import settings

app = FastAPI(title="RAG Knowledge Base API")

# 初始化 Chain (通常在启动时初始化一次即可，或者按需初始化)
rag_chain = get_rag_chain()

class Query(BaseModel):
    question: str

@app.post("/chat")
def chat(query: Query):
    # 直接调用封装好的 chain
    try:
        response = rag_chain.invoke(query.question)
        return {"answer": response}
    except Exception as e:
        return {"error": str(e)}

@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    # 使用配置中的路径
    save_path = settings.UPLOAD_DIR / file.filename

    with save_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "status": "success",
        "filename": file.filename,
        "message": "文件已上传，正在后台处理..."
    }
