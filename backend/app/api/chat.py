from fastapi import APIRouter, File, HTTPException, UploadFile, Form
from fastapi.responses import StreamingResponse
import json
import uuid
from datetime import datetime, timezone
from ..core.logging import logger
from ..models.schemas.responses.SessionCreationResponse import SessionCreationResponse
import shutil
import os

chat_router = APIRouter(prefix='/chat', tags=["chat"])

sessions: dict = {}
messages: dict = {}

# CREATE SESSION
@chat_router.post("/session", response_model=SessionCreationResponse)
async def create_session():
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)

    # Store session details in memory (or database)
    sessions[session_id] = {
        "id": session_id,
        "created_at": created_at,
        "updated_at": None
        }
    
    response = SessionCreationResponse(
        id=session_id,
        created_at=created_at,
        updated_at=None
    )

    logger.info(f"Created new session: {session_id}")

    return response

# SEND MESSAGE
@chat_router.post("/message")
async def send_message(
    session_id: str = Form(...),
    message_type: str = Form(...),
    text: str = Form(default=None),
    file: UploadFile = File(default=None),
    timestamp: datetime = Form(...),
):
    """Send a message to the chat"""
    
    # Validate session
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    file_path = None

    if file:
        # Create temp directory if not exists
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")

        try:
            # Save file locally for processing
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            logger.info(f"API: Received file {file.filename}. Request: {text}")

        except Exception as e:
            logger.error(f"Error saving uploaded file: {e}")
            raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    # Create user message
    user_message = {
        "message_id": str(uuid.uuid4()),
        "session_id": session_id,
        "role": "user",
        "messageType": message_type,
        "text": text,
        "attachments": file_path,
        "timestamp": timestamp,
    }
    
    messages[session_id] = [user_message]
    
    # IMPORTANT: Here you'll integrate with your LangGraph workflow
    # Example:
    # ai_response = await process_with_agents(text, file, message_type)
    
    # For now, return a mock AI response
    ai_message = {
        "message_id": str(uuid.uuid4()),
        "session_id": session_id,
        "role": "ai",
        "messageType": "text",
        "text": f"Processing: {text if text else 'File uploaded'}",
        "attachments": file_path,
        "timestamp": datetime.now(timezone.utc),
    }
    
    messages[session_id].append(ai_message)

    logger.info(f"Processed message for session {session_id}. User message: {text if text else 'File uploaded'}")

    # Cleanup the temp file after processing
    if os.path.exists(file_path):
         os.remove(file_path)
    
    return ai_message