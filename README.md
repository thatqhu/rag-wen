    cd backend
    uvicorn server:app --host 0.0.0.0 --port 8000 --reload

    cd frontend
    npm install & npm run dev

    3 nodes: agent_node, tool_node, reflection_node
    2 edges: route_agent -> (Tools OR Reflect), route_critique -> (Agent OR End)

    Ask quetion：
    what's the weather today?
    |
    #1, agent calls the llm, but there is no helpful message, route_agent will route to tool_node
    |
    #2, tool_node uses tool to search on web， return to agent_node again.
    |
    #3, agent_node got the message and it contains some special message, which needs to do a reflaction, not a llm call.
    |
    #4, reflection_node check the result
    |
    #5, route_critique check failed -> #2
    |
    #5，return the result to client
