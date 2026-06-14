import os
import json
import uuid
import asyncio
from datetime import datetime
from pathlib import Path

from mcp.server import Server
import mcp.types as types
from mcp.server.stdio import stdio_server


# ----------------------------
# Data Setup
# ----------------------------
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
KB_DIR = DATA_DIR / "knowledge_base"
TICKETS_FILE = DATA_DIR / "tickets" / "tickets.json"

KB_DIR.mkdir(parents=True, exist_ok=True)
TICKETS_FILE.parent.mkdir(parents=True, exist_ok=True)

# Keep SAME structure as FastMCP (dict)
if not TICKETS_FILE.exists():
    TICKETS_FILE.write_text("{}")


VALID_STATUSES = ["open", "in_progress", "resolved", "closed"]
VALID_PRIORITIES = ["low", "medium", "high"]


# ----------------------------
# Raw MCP Server
# ----------------------------
app = Server("IT-Service-Desk-Raw-MCP")


# ----------------------------
# Tool Definitions
# ----------------------------
@app.list_tools()
async def list_tools():
    return [
        types.Tool(
            name="search_knowledge_base",
            description="Search the local knowledge base for IT articles.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_all_open_tickets",
            description="Returns all open IT tickets.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="create_it_ticket",
            description="Create a new IT support ticket.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "user_email": {"type": "string"},
                    "priority": {"type": "string"},
                    "status": {"type": "string"},
                    "category": {"type": "string"}
                },
                "required": ["title", "description", "user_email"]
            }
        ),
        types.Tool(
            name="get_ticket_status",
            description="Fetch ticket details by ticket ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string"}
                },
                "required": ["ticket_id"]
            }
        ),
        types.Tool(
            name="update_ticket_status",
            description="Update an existing ticket status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string"},
                    "new_status": {"type": "string"}
                },
                "required": ["ticket_id", "new_status"]
            }
        ),
        types.Tool(
            name="escalate_ticket",
            description="Escalate a ticket to high priority.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["ticket_id", "reason"]
            }
        )
    ]


# ----------------------------
# Tool Router
# ----------------------------
@app.call_tool()
async def call_tool(name: str, arguments: dict):

    # SEARCH KNOWLEDGE BASE
    if name == "search_knowledge_base":
        query = arguments.get("query", "")
        results = []

        keywords = [word.lower() for word in query.split() if len(word) > 2]
        if not keywords:
            keywords = [query.lower()]

        for file_path in KB_DIR.glob("*.*"):
            if file_path.suffix in [".txt", ".md"]:
                content = file_path.read_text(encoding="utf-8")

                if any(
                    kw in file_path.name.lower() or kw in content.lower()
                    for kw in keywords
                ):
                    results.append(
                        f"--- Article: {file_path.name} ---\n{content}\n"
                    )

        if results:
            return [types.TextContent(type="text", text="\n".join(results))]

        return [
            types.TextContent(
                type="text",
                text=f"No knowledge base articles found matching '{query}'."
            )
        ]

    # GET OPEN TICKETS
    elif name == "get_all_open_tickets":
        try:
            tickets = json.loads(TICKETS_FILE.read_text(encoding="utf-8"))

            open_tickets = [
                t for t in tickets.values()
                if t.get("status") in ["open", "in_progress"]
            ]

            if not open_tickets:
                return [types.TextContent(type="text", text="No open tickets.")]

            output = "Open Tickets:\n"
            for t in open_tickets:
                output += (
                    f"- ID: {t.get('ticket_id')} | "
                    f"Title: {t.get('title')} | "
                    f"Status: {t.get('status')} | "
                    f"Priority: {t.get('priority')}\n"
                )

            return [types.TextContent(type="text", text=output)]

        except Exception as e:
            return [types.TextContent(type="text", text=str(e))]

    # CREATE TICKET
    elif name == "create_it_ticket":
        ticket_id = f"TKT-{str(uuid.uuid4())[:8].upper()}"

        new_ticket = {
            "ticket_id": ticket_id,
            "title": arguments.get("title"),
            "description": arguments.get("description"),
            "user_email": arguments.get("user_email"),
            "priority": arguments.get("priority", "medium").lower(),
            "category": arguments.get("category", "general").lower(),
            "status": arguments.get("status", "open").lower(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "notes": []
        }

        try:
            tickets = json.loads(TICKETS_FILE.read_text(encoding="utf-8"))
            tickets[ticket_id] = new_ticket

            TICKETS_FILE.write_text(
                json.dumps(tickets, indent=4),
                encoding="utf-8"
            )

            return [
                types.TextContent(
                    type="text",
                    text=f"Ticket successfully created! Ticket ID: {ticket_id}"
                )
            ]

        except Exception as e:
            return [types.TextContent(type="text", text=str(e))]

    # GET STATUS
    elif name == "get_ticket_status":
        ticket_id = arguments.get("ticket_id", "").upper()

        try:
            tickets = json.loads(TICKETS_FILE.read_text(encoding="utf-8"))
            ticket = tickets.get(ticket_id)

            if ticket:
                return [
                    types.TextContent(
                        type="text",
                        text=(
                            f"Ticket {ticket_id}\n"
                            f"Title: {ticket.get('title')}\n"
                            f"Status: {ticket.get('status')}\n"
                            f"Email: {ticket.get('user_email')}\n"
                            f"Priority: {ticket.get('priority')}"
                        )
                    )
                ]

            return [
                types.TextContent(
                    type="text",
                    text=f"Ticket '{ticket_id}' not found."
                )
            ]

        except Exception as e:
            return [types.TextContent(type="text", text=str(e))]

    # UPDATE STATUS
    elif name == "update_ticket_status":
        ticket_id = arguments.get("ticket_id", "").upper()
        new_status = arguments.get("new_status", "").lower()

        if new_status not in VALID_STATUSES:
            return [
                types.TextContent(
                    type="text",
                    text=f"Invalid status. Must be one of {VALID_STATUSES}"
                )
            ]

        try:
            tickets = json.loads(TICKETS_FILE.read_text(encoding="utf-8"))

            if ticket_id not in tickets:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Ticket '{ticket_id}' not found."
                    )
                ]

            tickets[ticket_id]["status"] = new_status
            tickets[ticket_id]["updated_at"] = datetime.utcnow().isoformat()

            TICKETS_FILE.write_text(json.dumps(tickets, indent=4))

            return [
                types.TextContent(
                    type="text",
                    text=f"Ticket {ticket_id} updated to {new_status}"
                )
            ]

        except Exception as e:
            return [types.TextContent(type="text", text=str(e))]

    # ESCALATE
    elif name == "escalate_ticket":
        ticket_id = arguments.get("ticket_id", "").upper()
        reason = arguments.get("reason", "")

        try:
            tickets = json.loads(TICKETS_FILE.read_text(encoding="utf-8"))

            if ticket_id not in tickets:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Ticket '{ticket_id}' not found."
                    )
                ]

            tickets[ticket_id]["status"] = "in_progress"
            tickets[ticket_id]["priority"] = "high"
            tickets[ticket_id]["updated_at"] = datetime.utcnow().isoformat()
            tickets[ticket_id]["notes"].append(f"ESCALATED: {reason}")

            TICKETS_FILE.write_text(json.dumps(tickets, indent=4))

            return [
                types.TextContent(
                    type="text",
                    text=f"Ticket {ticket_id} escalated successfully."
                )
            ]

        except Exception as e:
            return [types.TextContent(type="text", text=str(e))]

    else:
        raise ValueError(f"Unknown tool: {name}")


# ----------------------------
# Start Server
# ----------------------------
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())