"""
API routes for chatbot with RAG.

Endpoints:
- POST /chat - Chat with the AI
- DELETE /chat/session/{session_id} - Clear a chat session
- GET /chat/documents/count - Get document count

Note: File uploads moved to /files/upload (includes storage + RAG indexing)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import CurrentUser, get_current_user
from domain.chatbot.models import ChatRequest, ChatResponse
from domain.chatbot.service import ChatbotService, get_chatbot_service

router = APIRouter(prefix="/chat", tags=["chatbot"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: CurrentUser = Depends(get_current_user),
    service: ChatbotService = Depends(get_chatbot_service),
):
    """
    Chat with the AI assistant.
    
    The AI uses RAG to answer questions based on uploaded PDF documents.
    Conversation history is maintained per session.
    
    Args:
        message: Your question or message
        session_id: Optional - provide to continue a conversation
        
    Returns:
        AI response with session_id and source documents used
    """
    try:
        return service.chat(
            message=request.message,
            session_id=request.session_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat error: {str(exc)}",
        ) from exc


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    user: CurrentUser = Depends(get_current_user),
    service: ChatbotService = Depends(get_chatbot_service),
):
    """
    Clear a chat session's memory.
    
    This removes all conversation history for the given session.
    """
    cleared = service.clear_session(session_id)
    if not cleared:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    return {"message": "Session cleared", "session_id": session_id}


@router.get("/documents/count")
async def get_document_count(
    user: CurrentUser = Depends(get_current_user),
    service: ChatbotService = Depends(get_chatbot_service),
):
    """
    Get the number of document chunks in the knowledge base.
    """
    count = service.get_document_count()
    return {"chunk_count": count}


__all__ = ["router"]

