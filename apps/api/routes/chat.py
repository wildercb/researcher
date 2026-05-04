from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    content: str
    role: str = "user"


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


@router.post("/")
async def chat(request: ChatRequest) -> dict:
    # Stub — wired to agent runtime in Phase 3
    return {
        "response": "Atlas agent runtime not yet connected. This is a Phase 0 stub.",
        "agent": None,
        "tools_used": [],
        "cost_usd": 0.0,
    }
