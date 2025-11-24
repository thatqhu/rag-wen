import os
from typing import List, TypedDict, Literal, Annotated
import operator
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode

# --- 1. 定义状态 ---
# Annotated[List, operator.add] 是 LangGraph 的一个特性 (Reducer)
# 意思是：当节点返回 {"messages": [new_msg]} 时，不是覆盖，而是 append 到列表后面
# 这对 Elixir 程序员来说，就像是 Enum.concat(state.messages, new_messages)
class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    revision_count: int

# --- 2. 初始化工具和模型 ---
# 确保环境变量 TAVILY_API_KEY 已设置
tool = TavilySearchResults(max_results=3)
tools = [tool]

# bind_tools: 类似于 Elixir 的 Function Currying (柯里化)
# 我们告诉 LLM："你可以使用这些函数"
llm = ChatOpenAI(model="gpt-4o", temperature=0.5)
llm_with_tools = llm.bind_tools(tools)

# --- 3. 节点定义 ---

def agent_node(state: ChatState):
    """
    主 Agent：负责决定是 调用工具 还是 生成最终回复
    如果在'修改模式'下，它会看到 Critic 的意见并进行修正
    """
    print("--- Node: Agent ---")
    messages = state["messages"]

    # 定义系统提示词
    system_prompt = """你是一个智能研究助手。
    1. 如果用户的问题需要实时信息，请务必调用搜索工具。
    2. 如果收到了"编辑意见"，请根据意见修改你的上一轮回答。
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages")
    ])

    chain = prompt | llm_with_tools
    response = chain.invoke({"messages": messages})

    return {"messages": [response]}

def reflection_node(state: ChatState):
    """
    Critic：负责审查 Agent 的最终文本回复
    """
    print("--- Node: Critic ---")
    messages = state["messages"]
    last_message = messages[-1]

    # 这里我们要求回复必须详实，并且包含来源信息（如果用了搜索）
    reflection_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一名严格的主编。你的任务是审查 Agent 的回复。

        审查标准：
        1. 准确性：回答是否直接解决了用户的问题？
        2. 完整性：如果问题涉及事实，回答是否足够详细？
        3. 格式：回答必须包含至少一个 Emoji 来保持亲切感。

        如果通过，请仅输出 "APPROVE"。
        如果不通过，请输出具体的修改建议 (Start with "编辑意见:")。
        """),
        ("human", "Agent 的回复: \n\n {ai_response}")
    ])

    chain = reflection_prompt | llm
    critique = chain.invoke({"ai_response": last_message.content})

    return {"messages": [HumanMessage(content=critique.content)]}

# --- 4. 边的逻辑 (Routing) ---

def route_agent(state: ChatState):
    """
    决定 Agent 之后的去向：
    1. 有 Tool Calls -> 去 ToolNode
    2. 纯文本 -> 去 Reflection
    """
    last_message = state["messages"][-1]

    # 检查最后一条消息是否包含工具调用请求
    if last_message.tool_calls:
        return "tools"
    return "reflect"

def route_critique(state: ChatState):
    """
    决定 Reflection 之后的去向
    """
    last_message = state["messages"][-1]

    if "APPROVE" in last_message.content:
        return "end"

    # 防止死循环机制
    if state.get("revision_count", 0) > 3:
        return "end"

    return "retry"

# --- 5. 构建图 ---
workflow = StateGraph(ChatState)

# 添加节点
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools)) # 使用 LangGraph 预置的工具节点
workflow.add_node("reflect", reflection_node)

# 定义流程
workflow.add_edge(START, "agent")

# 关键路由 1: Agent -> (Tools OR Reflect)
workflow.add_conditional_edges(
    "agent",
    route_agent,
    {
        "tools": "tools",
        "reflect": "reflect"
    }
)

# 工具执行完，必须自动回 Agent 继续思考
workflow.add_edge("tools", "agent")

# 关键路由 2: Reflect -> (Agent OR End)
workflow.add_conditional_edges(
    "reflect",
    route_critique,
    {
        "retry": "agent", # 被打回，重写
        "end": END
    }
)

graph = workflow.compile()
