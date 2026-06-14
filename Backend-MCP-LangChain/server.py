import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import chat

app = FastAPI(
    title="IT Service Desk API",
    description="MCP-powered IT Service Desk",
    version="1.0.0",
)

# Allow all origins so the MCP Inspector (and future React frontend) can connect easily
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "IT Service Desk MCP"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)