import os
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from tools import (
    search_knowledge_base,
    get_all_open_tickets,
    create_it_ticket,
    get_ticket_status,
    update_ticket_status,
    escalate_ticket,
)

AGENT_NAME = "IT Service Desk LangChain-Agent (Native)"
SYSTEM_PROMPT = "You are an IT Service Desk Agent. Always search the knowledge base before creating tickets. and Also show ticket number if ticket created"

async def run_agent(user_message: str, history: list[dict] = None) -> str:

    # 1. Initialize Azure OpenAI via LangChain
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )

    # 2. Collect Langchain native tools
    tools = [
        search_knowledge_base,
        get_all_open_tickets,
        create_it_ticket,
        get_ticket_status,
        update_ticket_status,
        escalate_ticket,
    ]

    # 3. Create the LangGraph ReAct agent (the state machine)
    agent = create_react_agent(llm, tools)

    # 4. Format the incoming web UI session history array into LangChain Messages
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    if history:
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=user_message))

    # 5. Execute the agentic loop
    response = await agent.ainvoke({"messages": messages})

    # 6. Extract the final text answer directly from the end of the state graph array
    return response["messages"][-1].content