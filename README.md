# SalesLens AI

**SalesLens AI** is an intelligent, multi-agent conversational SaaS platform built to seamlessly integrate with CRM systems. Designed specifically to empower sales professionals, it serves multiple users across various domains by transforming how they interact with their data, client notes, and leads. 

By providing an advanced chatbot interface that supports text, voice, and multi-modal document uploads, SalesLens AI acts as a dedicated co-pilot for the modern salesperson.

## 🎯 Project Vision & Core Constraints

Based on the core needs of a salesperson, we have scoped the functionality to remain strictly sales-centric:
- **Session-Based Context:** Chat sessions are self-contained. Uploaded documents and images are processed in-memory for the current session. When a session ends, the AI generates a summary text file to preserve context for future days, avoiding unnecessary vector embedding of raw session data.
- **Explicit Lead Searching:** Lead matching is a deliberate action. Salespeople click "Search Leads" and provide a query to search the Vector Database (Qdrant).
- **Voice Integrations:**
  - *Record:* Uses ASR to transcribe audio and insert it directly into the text input.
  - *Live Voice:* Full STT/TTS bidirectional conversation allowing the user to search leads and query documents hands-free.

## ✨ Core Features & The UI Interface

Based on the initial wireframes, the intuitive interface focuses on a "What can I help you with?" chat experience.
1. **Omnichannel Input:**
   - **Text Query:** "Ask anything related to your work."
   - **Voice Options:** A Record button for asynchronous transcription, and a Live Voice button for real-time conversation.
2. **Action Buttons:**
   - **Upload (+):** Attach Images, PDFs, and Documents. The AI extracts data, summarizes large files, and answers questions based *only* on the uploaded files.
   - **Search Leads:** Explicitly queries the lead database.

## ⚙️ Architecture & Technology Stack

To ensure strict data privacy and enterprise-grade scalability, we utilize open-source models and self-hosted infrastructure:

- **Frontend:** React TypeScript providing the interactive chatbot UI, voice components, and document upload handlers.
- **Backend:** FastAPI handling multi-tenant logic, file parsing, and API endpoints.
- **AI Orchestration:** LangGraph and LangChain for parallel agent workflows, state management, and conversational routing.
- **LLM Serving & Routing:** 
  - *Serving:* High-throughput deployment engines like **vLLM** or **TGI (Text Generation Inference)** to serve open-source multimodal LLMs.
  - *Routing/Proxy:* **LiteLLM** or a similar gateway to handle model routing, failovers, and unified API access.
- **Data Infrastructure:** 
  - **Qdrant:** Vector database exclusively for the Lead Database.
  - **SQL Database:** Relational DB to store the raw 1,000 generated Egyptian leads before syncing to Qdrant.
  - **Redis:** Handles caching and strict rate-limiting per user/tenant.
- **Observability & DevOps:** 
  - **Langfuse:** For tracing SaaS tenant LLM usage and agent performance.
  - **Metrics & Logging:** Prometheus, Grafana, Loki, and Promtail.
  - **Deployment:** Dockerized containers deployed on AWS behind an NGINX reverse proxy.

---

*For detailed implementation steps, AI architecture, and sprint planning, please refer to the `implementation_plan.md` artifact.*
