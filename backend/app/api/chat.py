from fastapi import APIRouter, UploadFile, File, Form, HTTPException

# from ..models.schemas.ScoreRequest import AnalysisResponse
from ..core.logging import logger

chat_router = APIRouter(prefix='chat')

@chat_router.post("/session", response_model=create_chat_session_Response)
async def create_chat_session():
    # return { session_id: "uuid" }
    # response = {session_id: ""}
    # return response

@chat_router.post("/message", response_model=Send_Message_Response)
async def send_message(request: MessageRequest):
    #  MessageRequest = {     
    #    session_id: string,  
    #    message_type: 'text'|'image'|'audio'|'document',
    #    text?: string,
    #    file?: File,
    #    timestamp: ISO string
    #  }

    message_type =  MessageRequest['message_type']

    if message_type == 'text':
        response = ai_agent(message = MessageRequest['text'])
    elif message_type == 'image':
        #encode the image
        # send to VLM
        response = ai_agent(message = MessageRequest['text'], MessageRequest['file'])
    elif message_type == 'document':
        # send to llm
        response = ai_agent(message = MessageRequest['text'], MessageRequest['file'])
    else:
        #encode the audio
        # send to Speach LLM
        response = ai_agent(message = MessageRequest['text'], MessageRequest['file'])




    # response model = {
    #       id: response.message_id,
    #       sessionId: response.session_id,
    #       role: 'ai',
    #       messageType: response.messageType,
    #       text: response.text,
    #       attachments: response.attachments,
    #       timestamp: response.timestamp,
    #       status: 'sent',
    #     }


│  SEND MESSAGE                                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ POST /chat/message                                       │   │
│  │ Body: FormData {                                         │   │
│  │   session_id: string,                                    │   │
│  │   message_type: 'text'|'image'|'audio'|'document',      │   │
│  │   text?: string,                                         │   │
│  │   file?: File,                                           │   │
│  │   timestamp: ISO string                                  │   │
│  │ }                                                         │   │
│  │ Response: ChatMessageResponse                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  FETCH SESSIONS                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ GET /chat/sessions                                       │   │
│  │ Response: ChatSession[]                                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  FETCH HISTORY                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ GET /chat/sessions/{sessionId}/messages                 │   │
│  │ Response: ChatMessageResponse[]                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ADDITIONAL ENDPOINTS                                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ POST   /chat/sessions/{id}/clear                         │   │
│  │ DELETE /chat/sessions/{id}                               │   │
│  │ POST   /chat/sessions/{id}/regenerate                    │   │
│  │ GET    /chat/stream?session_id=... (optional SSE)        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘