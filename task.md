# SalesLens AI - Execution Tasks

## Sprint 1: Core Foundation & Document QA
- **Backend Setup (FastAPI)**
- **Backend Setup (FastAPI)**
  - `[x]` Clean up ContentLens AI codebase (remove marketing agents).
  - `[x]` Setup structured JSON logging (e.g., `structlog`) to prepare for Loki/Grafana.
  - `[x]` Configure CORS, Environment variables (`pydantic-settings`), and exception handlers.
- **Authentication & Multi-Tenancy**
  - `[x]` Implement JWT-based authentication for users/tenants.
  - `[x]` Setup FastAPI dependency injection for extracting user/tenant context in all routes.
- **Document Processing Pipeline**
  - `[x]` Implement PDF parsing service (using PyMuPDF or pdfplumber).
  - `[x]` Implement Image OCR service (using Tesseract/pytesseract).
  - `[x]` Implement DOCX/TXT text extraction services.
- **AI & Orchestration**
  - `[x]` Setup basic LangChain/LangGraph router for incoming text.
  - `[x]` Build Document QA Agent (capable of extracting and answering questions strictly from uploaded text).
- **Frontend Setup (React/Vite)**
  - `[x]` Initialize project structure, routing, and global state management (e.g., Zustand/Context).
  - `[x]` Build layout components: `Sidebar`, `Header` (with tenant profile), `MainContent`.
  - `[x]` Build Chat UI components: `MessageList`, `MessageBubble`, `ChatInputBox`.
  - `[x]` Build Upload components: `FileDropzone`, `UploadProgressIndicator`.
  - `[x]` Integrate frontend API client with backend authentication and chat endpoints.

## Sprint 2: Session Memory, Rate Limiting & Caching
- **Backend Redis Integrations**
  - `[ ]` Setup Redis connection manager in FastAPI.
  - `[ ]` Implement Rate Limiting middleware (restrict messages per minute per tenant).
  - `[ ]` Implement caching for frequent semantic hits or raw document extractions.
- **Session Context Management**
  - `[ ]` Build session ID generation and tracking in backend.
  - `[ ]` Build LangGraph Session Manager to inject past chat history into the LLM context.
  - `[ ]` Implement Session Summarization Agent (triggers asynchronously on session close).
  - `[ ]` Save generated session summaries to local files (or Redis) and load them on new session creation.
- **Frontend Enhancements**
  - `[ ]` Build Session History UI (sidebar list of past chats).
  - `[ ]` Add UI feedback for Rate Limiting (warnings, disabled inputs).

## Sprint 3: Voice Integrations (ASR & STT/TTS)
- **Backend Audio Services**
  - `[ ]` Implement async audio upload endpoint for pre-recorded voice notes.
  - `[ ]` Integrate an ASR model (e.g., Whisper) to transcribe audio uploads into text.
  - `[ ]` Setup FastAPI WebSockets endpoint specifically for "Live Voice".
  - `[ ]` Build STT (Speech-to-Text) stream parser inside the WebSocket.
  - `[ ]` Build TTS (Text-to-Speech) pipeline to generate audio chunks from LangGraph's streaming output.
- **Frontend Voice Components**
  - `[ ]` Build `RecordButton` component (hold-to-record/tap-to-record using Web Audio API).
  - `[ ]` Build `LiveVoiceToggle` component.
  - `[ ]` Implement WebSocket client to capture microphone and stream bytes to backend.
  - `[ ]` Implement Audio Player to seamlessly play incoming TTS audio chunks.

## Sprint 4: The Lead Database & Qdrant Integration
- **Data Generation & Relational Storage**
  - `[ ]` Design SQLAlchemy ORM models for `Lead` (name, industry, pain points, etc.).
  - `[ ]` Setup PostgreSQL/SQLite via Alembic migrations.
  - `[ ]` Write script to generate 1,000 fake Egyptian leads and populate the SQL DB.
- **Vector DB (Qdrant)**
  - `[ ]` Setup Qdrant client connection.
  - `[ ]` Build embedding pipeline (e.g., using HuggingFace sentence-transformers).
  - `[ ]` Write sync script: Pull leads from SQL -> Embed text -> Push to Qdrant collection.
- **AI Lead Integration**
  - `[ ]` Build "Search Leads" Agent using LangChain Qdrant Retriever tool.
  - `[ ]` Update Router Agent to route to Lead Search when user intent or explicit button click dictates.
- **Frontend Lead UI**
  - `[ ]` Add "Search Leads" action button below chat input.
  - `[ ]` Build `LeadCard` component to render matched lead data cleanly inside the chat stream.

## Sprint 5: Privacy-First DevOps & Observability
- **Inference Infrastructure**
  - `[ ]` Setup vLLM or TGI for fast, self-hosted LLM inference.
  - `[ ]` Setup LiteLLM proxy container to route LangChain calls to the vLLM instance.
- **Dockerization**
  - `[ ]` Write Dockerfile for FastAPI backend.
  - `[ ]` Write multi-stage Dockerfile for React frontend (serving via NGINX).
  - `[ ]` Create master `docker-compose.yml` for FastAPI, Frontend, Redis, Qdrant, and SQL DB.
- **Observability Stack**
  - `[ ]` Integrate Langfuse SDK into FastAPI/LangGraph for tracing agent execution and tokens.
  - `[ ]` Setup Prometheus metrics endpoint in FastAPI.
  - `[ ]` Deploy Grafana and configure dashboards (API latency, LLM tokens, Redis hits).
  - `[ ]` Setup Promtail and Loki to aggregate the structured JSON logs.
