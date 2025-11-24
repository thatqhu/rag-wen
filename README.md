#### A Simple real-time chatbox with refletion
    Create .env file, then add
    DASHSCOPE_API_KEY=
    TAVILY_API_KEY =

    docker-compose up -d

    Use vscode to attach in docker, then run:

    cd backend
    uvicorn server:app --host 0.0.0.0 --port 8000 --reload

    cd frontend
    npm install & npm run dev

    3 nodes: agent_node, tool_node, reflection_node
    2 edges: route_agent -> (Tools OR Reflect), route_critique -> (Agent OR End)

    Ask quetion：get the weather for NewYork city
    |
    #1, agent calls the llm, but there is no `real-time` message, route_agent will route to tool_node
    |
    #2, tool_node uses tool to search on web， return to agent_node again.
    |
    #3, agent_node got the message and do a reflaction
    |
    #4, reflection_node check the result, route_critique check failed -> #2
    |
    #5，return the result to client

    Ask quetion：1 + 1 equals to
    |
    #1, agent calls the llm, got response
    |
    #2, route_agent got the message and do a reflaction
    |
    #4, reflection_node check the result, route_critique check failed -> #2
    |
    #5，return the result to client
