from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from typing import List, Optional
from app.api.dependencies.auth import get_current_user, UserContext
from app.services.chat_service import ChatService
from app.models.schemas.responses.SessionMessagesResponse import (
    SessionResponse,
    MessageResponse
)

router = APIRouter()

@router.post("/session", response_model=SessionResponse)
async def create_session(current_user: UserContext = Depends(get_current_user)):
    """Create a new chat session"""
    res = await ChatService.create_session(current_user.user_id)
    return SessionResponse(
        id=res["id"],
        title=res["title"],
        messageCount=res["messageCount"],
        created_at=res["created_at"]
    )

@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(current_user: UserContext = Depends(get_current_user)):
    """Get all chat sessions"""
    res_list = await ChatService.get_sessions()
    return [
        SessionResponse(
            id=s["id"],
            title=s["title"],
            messageCount=s["messageCount"],
            created_at=s["created_at"],
            updated_at=s["updated_at"]
        ) for s in res_list
    ]

@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(session_id: str, current_user: UserContext = Depends(get_current_user)):
    """Get all messages for a specific session"""
    raw_messages = await ChatService.get_messages(session_id)
    return [
        MessageResponse(
            message_id=m["message_id"],
            session_id=m["session_id"],
            role=m["role"],
            messageType=m["messageType"],
            text=m["text"],
            attachments=m["attachments"],
            timestamp=m["timestamp"]
        ) for m in raw_messages
    ]

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, current_user: UserContext = Depends(get_current_user)):
    """Delete a chat session"""
    await ChatService.delete_session(session_id)
    return {"status": "deleted"}

@router.post("/sessions/{session_id}/clear")
async def clear_session(session_id: str, current_user: UserContext = Depends(get_current_user)):
    """Clear all messages in a session but keep the session alive"""
    await ChatService.clear_session(session_id)
    return {"status": "cleared"}

@router.post("/message", response_model=MessageResponse)
async def send_message(
    session_id: str = Form(...),
    message_type: str = Form(...),
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: UserContext = Depends(get_current_user)
):
    """Send a message and get an AI response from the document/chat context"""
    ai_msg = await ChatService.send_message(
        session_id=session_id,
        message_type=message_type,
        text=text,
        file=file,
        user_id=current_user.user_id
    )
    return MessageResponse(
        message_id=ai_msg["message_id"],
        session_id=session_id,
        role="ai",
        messageType="text",
        text=ai_msg["text"],
        attachments=[],
        timestamp=ai_msg["timestamp"]
    )

@router.post("/sessions/{session_id}/regenerate", response_model=MessageResponse)
async def regenerate_response(session_id: str, current_user: UserContext = Depends(get_current_user)):
    """Regenerate the last AI response"""
    ai_msg = await ChatService.regenerate_response(session_id)
    return MessageResponse(
        message_id=ai_msg["message_id"],
        session_id=session_id,
        role="ai",
        messageType="text",
        text=ai_msg["text"],
        attachments=[],
        timestamp=ai_msg["timestamp"]
    )
