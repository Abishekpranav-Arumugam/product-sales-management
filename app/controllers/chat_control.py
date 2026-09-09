from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.service.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


def get_chat_service() -> ChatService:
    return ChatService()


@router.post(
    "/",
    response_model=ChatResponse,
    summary="Ask a sales question",
    description=(
        "Understand natural-language sales questions and return a "
        "friendly answer."
    ),
    responses={500: {"description": "Internal server error"}},
)
def ask_chatbot(
    payload: ChatRequest,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> dict[str, Any]:
    try:
        return service.process_user_query(payload.message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
