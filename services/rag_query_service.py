from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import chromadb
import logging
from config.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Query Service")

class QueryRequest(BaseModel):
    question: str
    top_k: int = 4

class QueryResponse(BaseModel):
    answer: str
    source_documents: list

class RAGQueryService:
    """RAG查询服务，提供问答接口"""

    def __init__(self):
        # 初始化嵌入模型
        self.embeddings = HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL
        )

        # 连接Chroma
        chroma_client = chromadb.HttpClient(
            host=Config.CHROMA_HOST,
            port=Config.CHROMA_PORT
        )

        # 初始化向量存储
        self.vector_store = Chroma(
            client=chroma_client,
            collection_name=Config.CHROMA_COLLECTION,
            embedding_function=self.embeddings
        )

        # 初始化LLM
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=0.7,
            openai_api_key=Config.OPENAI_API_KEY
        )

        # 自定义提示模板
        prompt_template = """你是一个智能助手。基于以下上下文信息回答用户问题。
如果上下文中没有相关信息，请如实说明。

上下文：
{context}

问题：{question}

回答："""

        self.prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )

        # 创建RAG链
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(
                search_kwargs={"k": Config.RETRIEVAL_K}
            ),
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.prompt}
        )

        logger.info("RAG Query Service初始化完成")

    def query(self, question: str, top_k: int = 4):
        """
        执行RAG查询

        Args:
            question: 用户问题
            top_k: 检索的文档数量

        Returns:
            答案和来源文档
        """
        try:
            # 更新检索参数
            self.qa_chain.retriever.search_kwargs["k"] = top_k

            # 执行查询
            result = self.qa_chain.invoke({"query": question})

            # 格式化来源文档
            sources = [
                {
                    "content": doc.page_content[:200],
                    "metadata": doc.metadata
                }
                for doc in result['source_documents']
            ]

            return {
                "answer": result['result'],
                "source_documents": sources
            }

        except Exception as e:
            logger.error(f"查询失败: {e}")
            raise

# 初始化服务
rag_service = RAGQueryService()

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """查询接口"""
    try:
        result = rag_service.query(request.question, request.top_k)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

# 运行服务
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
