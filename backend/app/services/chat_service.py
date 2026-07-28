import uuid
import structlog
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import UploadFile, HTTPException

from app.services.document_parser import DocumentParserService
from app.agents.doc_qa_agent import DocumentQAAgent

logger = structlog.get_logger(__name__)

# In-memory storage for development (Sprint 1)
sessions_db: Dict[str, Dict[str, Any]] = {}
messages_db: Dict[str, List[Dict[str, Any]]] = {}

class ChatService:
    @staticmethod
    async def create_session(user_id: str) -> Dict[str, Any]:
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
        
        logger.info("Created chat session", session_id=session_id, user_id=user_id)
        return {
            "id": session_id,
            "title": "New Chat",
            "messageCount": 0,
            "created_at": now
        }

    @staticmethod
    async def get_sessions() -> List[Dict[str, Any]]:
        sessions_list = []
        for sid, sinfo in sessions_db.items():
            msg_count = len(messages_db.get(sid, []))
            sessions_list.append({
                "id": sid,
                "title": sinfo["title"],
                "messageCount": msg_count,
                "created_at": sinfo["created_at"],
                "updated_at": sinfo["updated_at"]
            })
        sessions_list.sort(key=lambda x: x["created_at"], reverse=True)
        return sessions_list

    @staticmethod
    async def get_messages(session_id: str) -> List[Dict[str, Any]]:
        if session_id not in sessions_db:
            raise HTTPException(status_code=404, detail="Session not found")
        return messages_db.get(session_id, [])

    @staticmethod
    async def delete_session(session_id: str) -> None:
        if session_id not in sessions_db:
            raise HTTPException(status_code=404, detail="Session not found")
        sessions_db.pop(session_id, None)
        messages_db.pop(session_id, None)
        logger.info("Deleted session", session_id=session_id)

    @staticmethod
    async def clear_session(session_id: str) -> None:
        if session_id not in sessions_db:
            raise HTTPException(status_code=404, detail="Session not found")
        messages_db[session_id] = []
        sessions_db[session_id]["document_text"] = ""
        sessions_db[session_id]["title"] = "Cleared Chat"
        logger.info("Cleared messages in session", session_id=session_id)

    @staticmethod
    async def send_message(
        session_id: str,
        message_type: str,
        text: Optional[str],
        file: Optional[UploadFile],
        user_id: str
    ) -> Dict[str, Any]:
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
        doc_qa_agent = DocumentQAAgent()
        
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
        
        return ai_msg

    @staticmethod
    async def regenerate_response(session_id: str) -> Dict[str, Any]:
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
        user_idx = -1
        for idx, m in enumerate(messages):
            if m["message_id"] == last_user_msg["message_id"]:
                user_idx = idx
                break
                
        if user_idx != -1:
            messages_db[session_id] = messages[:user_idx + 1]
        
        # Call send_message again internally (or just invoke doc_qa_agent)
        doc_context = session.get("document_text", "").strip()
        query = last_user_msg["text"] or "Extract data and summarize this document"
        doc_qa_agent = DocumentQAAgent()
        
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
        session["updated_at"] = datetime.now(timezone.utc)
        
        return ai_msg
