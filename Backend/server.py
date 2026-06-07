from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.chat import router as chat_router

# 1. Import the shared MCP instance
from mcp_instance import mcp

# 2. Import tools to trigger their @mcp.tool() registration
import tools.create_ticket
import tools.get_ticket_status
import tools.search_knowledge_base
import tools.escalate_ticket
import tools.list_tickets

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensures FastMCP cleans up sessions when the server shuts down
    async with mcp.session_manager.run():
        yield

app = FastAPI(
    title="IT Service Desk API",
    description="MCP-powered IT Service Desk",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow all origins so the MCP Inspector (and future React frontend) can connect easily
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the standard REST API routes for your React frontend
app.include_router(chat_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "IT Service Desk MCP"}

# Mount the MCP server to the root to avoid 307 redirect/trailing slash issues.
# NOTE: Because this is a catch-all route ("/") it MUST be the very last route registered in this file.
app.mount("/", mcp.streamable_http_app())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)