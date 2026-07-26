# SalesLens AI - Implementation Plan

Transform SalesLens AI into a SaaS CRM-integrated salesperson assistant with voice capabilities, document QA, and semantic lead search, deployed on self-hosted AWS infrastructure using open-source models for strict data privacy.

## User Review Required

> [!IMPORTANT]
> Please review the AI Architecture Design and the Sprint sequencing below. Let me know if the prioritization of features from easiest to hardest aligns with your go-to-market strategy.

## Open Questions

> [!NOTE]
> 1. **Open-Source Models:** Do we have a preferred open-source multimodal model in mind for deployment on vLLM/TGI (e.g., LLaVA, Qwen-VL, or Pixtral) to handle the image upload and OCR tasks?
> 2. **Live Voice Streaming:** For the "Live Voice" feature, should we use WebSockets in FastAPI to stream the STT directly to the LLM, and stream the TTS audio back to the React frontend to minimize conversational latency?

## AI Architecture Design

To ensure enterprise-grade privacy and multi-tenant scalability, the AI architecture moves away from local Ollama to a robust, self-hosted deployment stack.

### 1. Request Gateway & Routing
- **NGINX:** Acts as the entry point, handling SSL termination and reverse proxying to the FastAPI backend.
- **FastAPI:** Manages user authentication, multi-tenancy context, file uploads, and WebSocket connections for live voice.
- **LiteLLM (API Gateway):** Sits between LangChain and the Inference Engines. It provides a unified OpenAI-compatible endpoint, handles model routing, load balancing, and fallback logic if an inference node goes down.

### 2. Inference Layer (Self-Hosted)
- **vLLM / Text Generation Inference (TGI):** High-throughput, optimized inference servers hosting open-source LLMs (e.g., Llama-3) and Multimodal models for strict data privacy.

### 3. Orchestration & State (LangGraph & LangChain)
- **The Router Agent:** Analyzes the text/transcribed input. If the user clicks "Search Leads," it bypasses document QA and routes to the Lead Search tool. Otherwise, it defaults to Document Extraction/QA.
- **Session Memory Manager:** In-memory context during an active chat. Once the session ends, a summarization chain condenses the conversation and writes it to a `.txt` file tied to the session ID. Next time the user connects, this summary is loaded as the initial prompt context.

### 4. Data Infrastructure
- **Redis:** 
  - *Rate Limiting:* Enforces message/token limits per user/tenant.
  - *Caching:* Caches exact semantic hits or frequent document extractions to save GPU cycles.
- **Lead Storage:** 
  - *SQL DB:* Stores the raw 1,000 Egyptian leads (structured data).
  - *Qdrant (VDB):* Embeds the SQL lead descriptions. When a user queries "Search Leads", Qdrant performs the semantic similarity search.

### 5. Observability Stack
- **Langfuse:** Traces LangGraph executions, token usage per tenant, and agent quality.
- **Prometheus & Grafana:** Monitors API latency, vLLM GPU memory usage, and Redis hit rates.
- **Loki & Promtail:** Aggregates container logs across the AWS deployment.

---

## Sprints Breakdown (Easiest to Hardest)

### Sprint 1: Core Foundation & Document QA (The Basics)
*Difficulty: Low*
- Clean up the old ContentLens AI codebase to remove marketing agents.
- Setup FastAPI + React boilerplate with the new chat interface UI.
- Implement file uploads (PDF, DOCX, Images).
- Build the basic LangChain Router to answer questions, extract data, and summarize *only* the uploaded files.

### Sprint 2: Session Memory & Rate Limiting
*Difficulty: Low-Medium*
- Integrate Redis for user rate-limiting (e.g., Max X messages per minute).
- Implement the Session Manager: Keep context during the chat, and trigger an LLM summarization call when the session closes.
- Save the session summary to a text file and implement logic to inject it into the next day's chat context.

### Sprint 3: The Lead Database & Qdrant Integration
*Difficulty: Medium*
- Generate 1,000 fake leads in Egyptian Arabic.
- Build the SQL Database to store them and write a synchronization script to embed and push them to Qdrant.
- Connect the "Search Leads" UI button to a specific LangChain Agent that queries Qdrant and returns the matches to the chat.

### Sprint 4: Voice Integrations (ASR & STT/TTS)
*Difficulty: Hard*
- Integrate an open-source ASR model (e.g., Whisper) into FastAPI to handle the "Record" button uploads and transcribe them into the text panel.
- Implement the "Live Voice" pipeline: Establish a bidirectional connection (preferably WebSockets) to receive streaming audio, transcribe it, process it through LangGraph, and stream TTS (Text-to-Speech) audio back to the frontend.

### Sprint 5: Privacy-First DevOps & Deployment
*Difficulty: Hardest (Infrastructure)*
- Dockerize all components (Frontend, Backend, Redis, SQL, Qdrant).
- Setup the Inference Layer: Deploy vLLM/TGI and LiteLLM proxy on AWS GPU instances.
- Setup the Observability Stack: Deploy Prometheus, Grafana, Loki, Promtail, and Langfuse.
- Configure NGINX reverse proxy and load balancing for production traffic.

## Verification Plan
1. **Local Docker Compose:** Verify that all microservices (FastAPI, Redis, Qdrant) spin up locally without the heavy AWS infrastructure.
2. **Agent Unit Tests:** Ensure the Router correctly isolates Document QA from Lead Search based on button clicks.
3. **Load Testing:** Use tools like Locust to verify Redis rate limiting works and the LiteLLM proxy correctly queues requests to vLLM.
