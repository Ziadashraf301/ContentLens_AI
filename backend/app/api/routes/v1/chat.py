from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import os

from app.api.dependencies.auth import get_current_user, UserContext
from app.services.document_parser import DocumentParserService
from app.agents.doc_qa_agent import DocumentQAAgent
import structlog
from app.models.schemas.responses.SessionMessagesResponse import (
    SessionResponse,
    MessageResponse
)

logger = structlog.get_logger(__name__)
router = APIRouter()
doc_qa_agent = DocumentQAAgent()

# In-memory storage for development (Sprint 1)
# Structure: { session_id: { "id": str, "created_at": datetime, "updated_at": datetime, "document_text": str } }
sessions_db: Dict[str, Dict[str, Any]] = {}
# Structure: { session_id: [ message_objects ] }
messages_db: Dict[str, List[Dict[str, Any]]] = {}

@router.post("/session", response_model=SessionResponse)
async def create_session(current_user: UserContext = Depends(get_current_user)):
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    sessions_db[session_id] = {
        "id": session_id,
        "title": "New Chat",
        "created_at": now,
        "updated_at": now,
        "document_text": ""
    }
    messages_db[session_id] = []
    
    logger.info("Created chat session", session_id=session_id, user_id=current_user.user_id)
    return SessionResponse(
        id=session_id,
        title="New Chat",
        messageCount=0,
        created_at=now
    )

@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(current_user: UserContext = Depends(get_current_user)):
    """Get all chat sessions"""
    sessions_list = []
    for sid, sinfo in sessions_db.items():
        msg_count = len(messages_db.get(sid, []))
        sessions_list.append(SessionResponse(
            id=sid,
            title=sinfo["title"],
            messageCount=msg_count,
            created_at=sinfo["created_at"],
            updated_at=sinfo["updated_at"]
        ))
    # Return sessions ordered by creation time decending
    sessions_list.sort(key=lambda x: x.created_at, reverse=True)
    return sessions_list

@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(session_id: str, current_user: UserContext = Depends(get_current_user)):
    """Get all messages for a specific session"""
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    
    raw_messages = messages_db.get(session_id, [])
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
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    
    sessions_db.pop(session_id, None)
    messages_db.pop(session_id, None)
    logger.info("Deleted session", session_id=session_id)
    return {"status": "deleted"}

@router.post("/sessions/{session_id}/clear")
async def clear_session(session_id: str, current_user: UserContext = Depends(get_current_user)):
    """Clear all messages in a session but keep the session alive"""
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages_db[session_id] = []
    sessions_db[session_id]["document_text"] = ""
    sessions_db[session_id]["title"] = "Cleared Chat"
    logger.info("Cleared messages in session", session_id=session_id)
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
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = sessions_db[session_id]
    
    # Process attachment if exists
    attachments = []
    if file:
        try:
            logger.info("Processing chat file attachment", filename=file.filename)
            file_text = await DocumentParserService.parse_file(file)
            if file_text:
                session["document_text"] = (session["document_text"] or "") + "\n" + file_text
                attachments.append({
                    "id": str(uuid.uuid4()),
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "size": file.size
                })
                logger.info("Successfully added text from attachment to session", 
                            filename=file.filename, 
                            session_id=session_id)
        except Exception as e:
            logger.error("Failed to parse attachment in chat", error=str(e))
            raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")
            
    # Save User message
    user_msg_id = str(uuid.uuid4())
    user_msg = {
        "message_id": user_msg_id,
        "session_id": session_id,
        "role": "user",
        "messageType": message_type,
        "text": text,
        "attachments": attachments,
        "timestamp": datetime.now(timezone.utc)
    }
    messages_db[session_id].append(user_msg)
    
    # Auto-update session title based on first user message
    is_first_msg = len(messages_db.get(session_id, [])) <= 1
    should_update_title = session["title"] in ("New Chat", "Cleared Chat") or is_first_msg
    
    if should_update_title:
        if text:
            # Clean lead search prefix if present
            display_text = text
            if display_text.startswith("[Lead Search] "):
                display_text = display_text[len("[Lead Search] "):]
            session["title"] = display_text[:40] + ("..." if len(display_text) > 40 else "")
        elif file:
            session["title"] = f"File: {file.filename[:30]}"
        
    # Generate AI Response
    ai_response_text = ""
    doc_context = session.get("document_text", "").strip()
    
    try:
        if doc_context:
            # Answer question from document context
            query = text if text else "Extract data and summarize this document"
            ai_response_text = await doc_qa_agent.answer_question(doc_context, query)
        else:
            # No document uploaded in this session yet
            if text:
                # Basic text reply using default LLM config
                ai_response_text = await doc_qa_agent.answer_question("No document provided.", text)
            else:
                ai_response_text = "Please upload a document or ask a question."
    except Exception as e:
        logger.error("Error generating AI response in chat", error=str(e))
        ai_response_text = f"Sorry, I encountered an error: {str(e)}"
        
    # Save AI message
    ai_msg_id = str(uuid.uuid4())
    ai_msg = {
        "message_id": ai_msg_id,
        "session_id": session_id,
        "role": "ai",
        "messageType": "text",
        "text": ai_response_text,
        "attachments": [],
        "timestamp": datetime.now(timezone.utc)
    }
    messages_db[session_id].append(ai_msg)
    session["updated_at"] = datetime.now(timezone.utc)
    
    return MessageResponse(
        message_id=ai_msg_id,
        session_id=session_id,
        role="ai",
        messageType="text",
        text=ai_response_text,
        attachments=[],
        timestamp=ai_msg["timestamp"]
    )

@router.post("/sessions/{session_id}/regenerate", response_model=MessageResponse)
async def regenerate_response(session_id: str, current_user: UserContext = Depends(get_current_user)):
    """Regenerate the last AI response"""
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = sessions_db[session_id]
    messages = messages_db[session_id]
    
    if not messages:
        raise HTTPException(status_code=400, detail="No messages in session to regenerate")
        
    # Find last user message
    last_user_msg = None
    for m in reversed(messages):
        if m["role"] == "user":
            last_user_msg = m
            break
            
    if not last_user_msg:
        raise HTTPException(status_code=400, detail="No user message found to regenerate response for")
        
    # Remove all messages after the last user message
    user_idx = messages.index(last_user_msg)
    messages_db[session_id] = messages[:user_idx + 1]
    
    # Call send_message again internally (or just invoke doc_qa_agent)
    doc_context = session.get("document_text", "").strip()
    query = last_user_msg["text"] or "Extract data and summarize this document"
    
    try:
        if doc_context:
            ai_response_text = await doc_qa_agent.answer_question(doc_context, query)
        else:
            ai_response_text = await doc_qa_agent.answer_question("No document provided.", query)
    except Exception as e:
        ai_response_text = f"Error regenerating response: {str(e)}"
        
    # Save AI message
    ai_msg_id = str(uuid.uuid4())
    ai_msg = {
        "message_id": ai_msg_id,
        "session_id": session_id,
        "role": "ai",
        "messageType": "text",
        "text": ai_response_text,
        "attachments": [],
        "timestamp": datetime.now(timezone.utc)
    }
    messages_db[session_id].append(ai_msg)
    
    return MessageResponse(
        message_id=ai_msg_id,
        session_id=session_id,
        role="ai",
        messageType="text",
        text=ai_response_text,
        attachments=[],
        timestamp=ai_msg["timestamp"]
    )
