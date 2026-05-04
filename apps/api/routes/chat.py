from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.deps import get_session
from packages.agents.router import route_message
from packages.core.models import ChatMessage as ChatMessageModel
from packages.core.models import Conversation

router = APIRouter(prefix="/api/chat", tags=["chat"])


class MessageIn(BaseModel):
    content: str
    role: str = "user"


class ChatRequest(BaseModel):
    messages: list[MessageIn]
    conversation_id: int | None = None


@router.get("/conversations/")
async def list_conversations(
    limit: int = 30, session: AsyncSession = Depends(get_session),
) -> dict:
    result = await session.execute(
        select(Conversation).order_by(Conversation.updated_at.desc()).limit(limit)
    )
    convos = result.scalars().all()
    return {
        "conversations": [
            {"id": c.id, "title": c.title,
             "created_at": c.created_at.isoformat() if c.created_at else None,
             "updated_at": c.updated_at.isoformat() if c.updated_at else None}
            for c in convos
        ]
    }


@router.get("/conversations/{convo_id}")
async def get_conversation(convo_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    result = await session.execute(select(Conversation).where(Conversation.id == convo_id))
    convo = result.scalar_one_or_none()
    if not convo:
        return {"error": "not found"}
    msg_result = await session.execute(
        select(ChatMessageModel).where(ChatMessageModel.conversation_id == convo_id)
        .order_by(ChatMessageModel.created_at)
    )
    messages = msg_result.scalars().all()
    return {
        "id": convo.id, "title": convo.title,
        "messages": [
            {"id": m.id, "role": m.role, "content": m.content,
             "agent": m.agent, "model": m.model, "cost_usd": m.cost_usd,
             "created_at": m.created_at.isoformat() if m.created_at else None}
            for m in messages
        ],
    }


@router.delete("/conversations/{convo_id}")
async def delete_conversation(convo_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    await session.execute(delete(ChatMessageModel).where(ChatMessageModel.conversation_id == convo_id))
    await session.execute(delete(Conversation).where(Conversation.id == convo_id))
    return {"status": "deleted"}


@router.post("/")
async def chat(request: ChatRequest, session: AsyncSession = Depends(get_session)) -> dict:
    if not request.messages:
        return {"response": "No messages provided.", "agent": None, "cost_usd": 0.0}

    convo_id = request.conversation_id
    if convo_id:
        result = await session.execute(select(Conversation).where(Conversation.id == convo_id))
        convo = result.scalar_one_or_none()
    else:
        convo = None

    if not convo:
        convo = Conversation(title=request.messages[0].content[:100])
        session.add(convo)
        await session.flush()
        convo_id = convo.id

    last_message = request.messages[-1]
    session.add(ChatMessageModel(
        conversation_id=convo_id, role=last_message.role, content=last_message.content,
    ))

    try:
        result = await route_message(last_message.content)
        response_text = result.get("response", "")
        session.add(ChatMessageModel(
            conversation_id=convo_id, role="assistant", content=response_text,
            agent=result.get("agent_used"), model=result.get("model"),
            cost_usd=result.get("cost_usd", 0),
        ))
        return {
            "response": response_text, "agent": result.get("agent_used"),
            "intent": result.get("intent"), "model": result.get("model"),
            "cost_usd": result.get("cost_usd", 0), "latency_ms": result.get("latency_ms", 0),
            "conversation_id": convo_id,
        }
    except Exception as e:
        error_msg = f"Agent runtime error: {e}. Check that LLM API keys are configured."
        session.add(ChatMessageModel(
            conversation_id=convo_id, role="assistant", content=error_msg,
        ))
        return {"response": error_msg, "agent": None, "cost_usd": 0.0, "conversation_id": convo_id}
