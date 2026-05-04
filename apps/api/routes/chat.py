from fastapi import APIRouter
from pydantic import BaseModel

from packages.agents.router import route_message

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    content: str
    role: str = "user"


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


@router.post("/")
async def chat(request: ChatRequest) -> dict:
    """Route a chat message to the appropriate agent."""
    if not request.messages:
        return {"response": "No messages provided.", "agent": None, "cost_usd": 0.0}

    last_message = request.messages[-1].content

    try:
        result = await route_message(last_message)
        return {
            "response": result.get("response", ""),
            "agent": result.get("agent_used"),
            "intent": result.get("intent"),
            "model": result.get("model"),
            "cost_usd": result.get("cost_usd", 0),
            "latency_ms": result.get("latency_ms", 0),
            "prompt_version": result.get("prompt_version"),
        }
    except Exception as e:
        return {
            "response": f"Agent runtime error: {e}. Check that LLM API keys are configured.",
            "agent": None,
            "cost_usd": 0.0,
        }
