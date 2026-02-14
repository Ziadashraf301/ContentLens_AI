from fastapi import APIRouter, File, HTTPException, UploadFile, Form
from fastapi.responses import StreamingResponse
import uuid
import os
from datetime import datetime, timezone

from ..models.schemas.helpers.MessageType import MessageType
from ..core.logging import logger
from ..models.schemas.responses.SessionCreationResponse import SessionCreationResponse
from ..utils.file_utils import save_file_locally
from ..workflows.chat_with_agents import run_chat_workflow

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
    message_type: MessageType = Form(...),
    text: str = Form(default=None),
    file: UploadFile = File(default=None),
    timestamp: datetime = Form(...),
):
    """Send a message to the chat"""
    
    # Validate session
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    file_path = None
    file_attachment = None  

    if file:
        # Create temp directory if not exists
        temp_dir = "temp_uploads"

        try:
            # Save file locally for processing
            file_path = await save_file_locally(temp_dir, file)
            logger.info(f"API: Received file {file.filename}. Request: {text}")
            
            # Create attachment object
            file_attachment = {
                "id": str(uuid.uuid4()),
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file.size,
                "path": file_path,
            }

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
        "attachments": [file_attachment] if file_attachment else [],
        "timestamp": timestamp,
    }
    
    messages[session_id] = [user_message]
    
    # Integrate with LangGraph workflow
    ai_response = await run_chat_workflow(
        user_request=text, 
        file_path=file_path,
        message_type=message_type, 
        tracer=None
    )
    
    # AI response message
    ai_message = {
        "message_id": str(uuid.uuid4()),
        "session_id": session_id,
        "role": "ai",
        "messageType": "text",
        "text": f"Processing: {ai_response['response'] if ai_response else 'No response generated'}",
        "attachments": [],
        "timestamp": datetime.now(timezone.utc),
    }
    
    messages[session_id].append(ai_message)

    logger.info(f"Processed message for session {session_id}. User message: {text if text else 'File uploaded'}")
    
    if file:
        # Cleanup the temp file after processing
        if os.path.exists(file_path):
            os.remove(file_path)
    
    return ai_message