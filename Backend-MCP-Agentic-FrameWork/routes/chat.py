from fastapi import APIRouter
from pydantic import BaseModel
from agent import AGENT_NAME, run_agent

# Set up the router with a clean prefix
router = APIRouter(prefix="/api", tags=["chat"])

# Define the expected JSON body from the frontend
class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []

# Define the expected JSON response sent back to the frontend
class ChatResponse(BaseModel):
    reply: str

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    print(f"[API] /api/chat request received | agent={AGENT_NAME}")
    
    # Pass the message and history to the Agentic Loop
    reply = await run_agent(
        user_message=request.message,
        history=request.history or None,
    )
    
    print(f"[API] /api/chat response sent | agent={AGENT_NAME}")
    return ChatResponse(reply=reply)