import os
from typing import List, TypedDict, Annotated
import operator
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from pydantic import SecretStr
from langgraph.checkpoint.memory import MemorySaver

class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    revision_count: int

tool = TavilySearchResults(max_results=3)
tools = [tool]
api_key_val = os.environ.get("DASHSCOPE_API_KEY")
if not api_key_val:
    raise ValueError("DASHSCOPE_API_KEY is not set")
llm = ChatOpenAI(
    model="qwen-plus",
    api_key=SecretStr(api_key_val),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.5
)
llm_with_tools = llm.bind_tools(tools)

# --- function nodes ---

def agent_node(state: ChatState):
    print("--- Node: Agent ---")
    messages = state["messages"]

    # Define system prompt
    # note, if we have `Editorial-Feedback`, we are not going to let reflection node to handle it
    # I think I need to optmize the prompt more.
    # However, I just want to demostrate the tool use here. So make sure ask the `English` question.
    system_prompt = """You are an intelligent research assistant.
    1. If the user's question requires current information, you must strictly call the search tool.
    2. If you receive 'Editorial-Feedback', please modify your previous response based on the feedback.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages")
    ])

    chain = prompt | llm_with_tools
    response = chain.invoke({"messages": messages})

    return {"messages": [response]}

def reflection_node(state: ChatState):
    print("--- Node: Critic ---")
    messages = state["messages"]
    last_message = messages[-1]

    reflection_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a strict editor-in-chief. Your task is to review the Agent's response.

        Review Criteria:
        1. Accuracy: Does the answer directly address the user's question?
        2. Completeness: If the question involves facts, is the answer detailed enough?

        If approved, please output "APPROVE" only.
        If not approved, please provide specific revision suggestions (Start with "Editorial-Feedback:").
        """),
        ("human", "Agent's response: \n\n {ai_response}")
    ])

    chain = reflection_prompt | llm
    critique = chain.invoke({"ai_response": last_message.content})

    return {"messages": [HumanMessage(content=critique.content)]}

# --- 4. edge logic (Routing) ---

def route_agent(state: ChatState):
    last_message = state["messages"][-1]
    # Check if the last message contains tool call requests
    if  isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "reflect"

def route_critique(state: ChatState):
    last_message = state["messages"][-1]

    if "APPROVE" in last_message.content:
        return "end"

    if state.get("revision_count", 0) > 3:
        return "end"

    return "retry"

# --- build graph ---
workflow = StateGraph(ChatState)

# add nodes
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("reflect", reflection_node)

# workflow entry point
workflow.add_edge(START, "agent")

workflow.add_conditional_edges(
    "agent",
    route_agent,
    {
        "tools": "tools",
        "reflect": "reflect"
    }
)

workflow.add_edge("tools", "agent")

workflow.add_conditional_edges(
    "reflect",
    route_critique,
    {
        "retry": "agent",
        "end": END # we may think about to save the ai result message to a final output here
    }
)

graph = workflow.compile()

memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
