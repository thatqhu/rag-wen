from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from .db import get_vector_store
from .config import settings

def format_docs(docs):
    """将检索到的文档列表转换为字符串，用换行符分隔"""
    return "\n\n".join(doc.page_content for doc in docs)

def get_rag_chain():
    """
    构建 RAG 处理链路
    数据流: Query -> Retriever -> Context + Query -> Prompt -> LLM -> String
    """

    # 1. 获取向量存储实例
    vector_store = get_vector_store()

    # 2. 转换为检索器 (Retriever)
    # search_kwargs={"k": 4}: 每次检索最相似的 4 个片段
    retriever = vector_store.as_retriever(
        search_kwargs={"k": settings.RETRIEVER_K}
    )

    # 3. 定义 Prompt 模板
    # 使用中文提示词，强调基于上下文回答
    template = """你是一个专业的企业知识库助手。请严格根据以下检索到的【上下文内容】回答用户的【问题】。
    如果上下文中没有包含答案，请直接回答“根据现有文档无法回答该问题”，不要尝试编造内容。

    【上下文内容】:
    {context}

    【问题】:
    {question}
    """

    prompt = ChatPromptTemplate.from_template(template)

    # 4. 初始化 LLM
    llm = ChatOpenAI(
        model=settings.LLM_MODEL_NAME,
        temperature=0.1,  # 降低随机性，让回答更准确
        api_key=settings.OPENAI_API_KEY
    )

    # 5. 组装 Chain (LCEL 语法)
    # RunnablePassthrough() 用于直接传递用户的原始问题
    rag_chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain
