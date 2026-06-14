import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import AzureChatOpenAI
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

AGENT_NAME = "IT Service Desk LangChain-Agent"
SYSTEM_PROMPT = "You are an IT Service Desk Agent. Always search the knowledge base before creating tickets."

async def run_agent(user_message: str, history: list[dict] = None) -> str:

    # 1. Initialize Azure OpenAI via LangChain
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )

    # 2. Configure the MCP standard I/O connection parameters
    server_path = Path(__file__).parent / "mcp_server.py"
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
    )

    # Context managers automatically handle connecting and disconnecting the subprocess
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 3. Fetch tool schemas from MCP and convert them to LangChain Tool objects
            tools = await load_mcp_tools(session)

            # 4. Create the LangGraph ReAct agent (the state machine)
            agent = create_react_agent(llm, tools)

            # 5. Format the incoming web UI session history array into LangChain Messages
            messages = [SystemMessage(content=SYSTEM_PROMPT)]

            if history:
                for msg in history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))

            messages.append(HumanMessage(content=user_message))

            # 6. Execute the agentic loop (it will loop between reasoning and tool calling automatically)
            response = await agent.ainvoke({"messages": messages})

            # 7. Extract the final text answer directly from the end of the state graph array
            return response["messages"][-1].content