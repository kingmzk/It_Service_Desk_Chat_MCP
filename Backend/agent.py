import json
import os
from openai import AsyncAzureOpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from dotenv import load_dotenv

load_dotenv()

AGENT_NAME = "IT Service Desk Agent"

# ── Azure OpenAI Config ───────────────────────────────────────
AZURE_ENDPOINT    = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_API_KEY     = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_DEPLOYMENT  = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4.1")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
MCP_SERVER_URL    = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")

SYSTEM_PROMPT = """You are an expert IT Service Desk assistant.

Your job is to help users with IT issues. Follow this workflow:
1. ALWAYS search the knowledge base first using search_knowledge_base.
2. If the KB article solves the issue, share the solution — do NOT create a ticket.
3. If the issue needs human intervention, create a ticket with create_ticket.
4. If a ticket already exists and the user asks for an update, use get_ticket_status.
5. If an issue is urgent/business-critical, use escalate_ticket.
6. To list open or filtered tickets, use list_tickets.

Always be concise, professional, and empathetic. When creating tickets, confirm the
ticket_id back to the user so they can track progress.
"""


async def _get_mcp_tools(session: ClientSession) -> list[dict]:
    """Fetch available tools from the MCP server and convert to OpenAI tool format."""
    tools_result = await session.list_tools()
    openai_tools = []
    for tool in tools_result.tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name":        tool.name,
                "description": tool.description or "",
                "parameters":  tool.inputSchema,
            },
        })
    print(f"[AGENT] Available MCP tools: {[t['function']['name'] for t in openai_tools]}")
    return openai_tools


async def _call_mcp_tool(session: ClientSession, name: str, arguments: dict) -> str:
    """Call an MCP tool and return the result as a JSON string."""
    print(f"[AGENT] Calling tool: {name} | args={arguments}")
    try:
        result = await session.call_tool(name, arguments)
        
        if result.isError:
            error_msg = f"Tool returned an error: {result.content}"
            print(f"[AGENT] {error_msg}")
            return json.dumps({"error": error_msg})

        if result.content:
            parts = []
            for block in result.content:
                if hasattr(block, "text"):
                    parts.append(block.text)
                elif isinstance(block, dict) and "text" in block:
                    parts.append(block["text"])
                else:
                    parts.append(str(block))
            
            tool_output = "\n".join(parts)
            preview = tool_output[:240].replace("\n", " ")
            print(f"[AGENT] Tool completed: {name} | preview={preview}")
            return tool_output
            
        # Fallback if FastMCP returns raw data instead of structured text blocks
        if hasattr(result, "value") and result.value is not None:
            tool_output = json.dumps(result.value)
            print(f"[AGENT] Tool completed: {name} | preview={tool_output[:240]}")
            return tool_output

        print(f"[AGENT] Tool completed: {name} | no content")
        return "{}"
        
    except Exception as e:
        print(f"[AGENT] Tool execution failed: {e}")
        return json.dumps({"error": str(e)})


async def run_agent(user_message: str, history: list[dict] | None = None) -> str:
    """
    Run the IT Service Desk agent for a single user turn.

    Args:
        user_message: The latest message from the user.
        history:      Previous conversation turns (list of OpenAI message dicts).

    Returns:
        The assistant's final text response.
    """
    print(f"[AGENT] Starting: {AGENT_NAME}")
    print(f"[AGENT] Model deployment: {AZURE_DEPLOYMENT}")
    print(f"[AGENT] User message: {user_message}")

    client = AsyncAzureOpenAI(
        azure_endpoint=AZURE_ENDPOINT,
        api_key=AZURE_API_KEY,
        api_version=AZURE_API_VERSION,
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    async with streamable_http_client(MCP_SERVER_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await _get_mcp_tools(session)

            # ── Agentic loop ──────────────────────────────────
            while True:
                response = await client.chat.completions.create(
                    model=AZURE_DEPLOYMENT,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                )

                choice = response.choices[0]

                # No tool call → final answer
                if choice.finish_reason == "stop":
                    final_text = choice.message.content or ""
                    print(f"[AGENT] Response completed by: {AGENT_NAME}")
                    return final_text

                # Tool call(s) requested
                if choice.finish_reason == "tool_calls":
                    print(f"[AGENT] LLM requested tool calls: {len(choice.message.tool_calls or [])}")
                    assistant_msg = choice.message
                    messages.append(assistant_msg)

                    for tool_call in assistant_msg.tool_calls:
                        fn_name = tool_call.function.name
                        fn_args = json.loads(tool_call.function.arguments)

                        tool_result = await _call_mcp_tool(session, fn_name, fn_args)

                        messages.append({
                            "role":         "tool",
                            "tool_call_id": tool_call.id,
                            "content":      tool_result,
                        })

                    continue

                break

    print(f"[AGENT] Fallback response returned by: {AGENT_NAME}")
    return "Sorry, I was unable to process your request. Please try again."