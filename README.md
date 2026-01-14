# ContentLens AI

![CI](https://github.com/Ziadashraf301/ContentLens_AI/actions/workflows/ci.yml/badge.svg)

**ContentLens AI** is a developer-focused open-source toolkit for extracting, analyzing, and summarizing information from documents using modern LLMs and document-processing tools. It provides a FastAPI backend that processes uploads (PDF, DOCX, TXT, images), runs an LLM-based workflow for extraction, summarization, translation, and analysis, and a React-based frontend for uploading files and visualizing results.

![ContentLens AI Logo](images/ContentLens_AI.png)

---

## 🔍 Project Purpose

ContentLens AI helps developers and teams quickly gain insights from unstructured documents. It is designed for:

- Document analysis and information extraction (text, tables, metadata)
- Summarization and intent-based question answering
- OCR for scanned documents and images
- Translating and analyzing documents into actionable insights
- Providing a simple web UI and REST API to integrate into applications

---

## 🎯 Intended Use & Marketing Focus

**Important:** This multi-agent system is designed to help marketing teams rapidly prototype and build document-driven marketing materials, generate summaries and insights, and accelerate content development for authorized campaigns. It is suitable for content ideation, internal research, and marketing asset production when used responsibly.

Please follow these responsible marketing guidelines:
- **Consent & opt-in:** Only use content and data for marketing when you have explicit consent or a lawful basis; do not use the tool to send unsolicited messages or spam.
- **No targeted deception:** Avoid using outputs to manipulate, deceive, or covertly profile individuals for targeted persuasion.
- **Privacy & data minimization:** Do not upload sensitive PII or regulated data unless strictly necessary and properly secured.
- **Human review & QA:** Always review, edit, and fact-check generated content to ensure brand alignment and accuracy.
- **Compliance & transparency:** Adhere to applicable marketing regulations, platform policies, and transparently disclose AI-assisted content when required.

---

## ✨ Features

- REST API to upload and process documents (multipart file uploads)
- LangChain / LangGraph-based workflows that orchestrate extractors, analyzers, and summarizers
- OCR support (via Tesseract) for scanned images and PDFs
- Configurable LLM settings (Ollama models configurable via env vars)
- Recommendation engine for prioritized, actionable suggestions
- Marketing agent support (ideation, copywriting, compliance checks) to accelerate marketing workflows
- Observability integration (Langfuse hooks are available in config)
- Lightweight React frontend with file uploader and results page
- Tests and logging

---

## 🚀 Quick Start

Prerequisites

- Python 3.11+ (recommended)
- Node.js 16+ / npm or Yarn for the frontend
- Tesseract OCR installed and accessible in PATH (for OCR features)
- Ollama or another supported LLM runtime running if you plan to use local LLMs

Backend (development)

1. Create a Python virtual environment and activate it:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

2. Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

3. Create a `.env` file in `backend/` (see Configuration below) and adjust values.

4. Run the backend with Uvicorn (from project root):

```bash
# From project root
cd backend
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/ — you should see a JSON response confirming the backend is running.

Frontend (development)

1. Install Node dependencies:

```bash
cd frontend
npm install
# or
# yarn
```

2. Start the development server:

```bash
npm start
```

Open the UI at http://localhost:3000 by default, or visit your deployed domain. For production, prefer using a DNS name (e.g., https://app.example.com) and keep `REACT_APP_API_URL` blank so the frontend uses same-origin relative API paths.

---

## 🧪 Running Tests

Backend tests are implemented under `backend/tests/`.

```bash
# from project root
pip install pytest
pytest backend/tests -q
```

(If you use a test runner or CI, adjust these commands accordingly.)

---

## ⚙️ Configuration

Configuration is centralized in `backend/app/core/config.py` and can be overridden via a `.env` file in the backend folder. Important settings:

- APP_NAME — application name
- ENV — `development` or `production`
- LOG_LEVEL — logging verbosity
- OLLAMA_BASE_URL — URL for the Ollama runtime (default: http://localhost:11434)
- OLLAMA_MODEL_* — model names used for different tasks (extractor, router, summarizer, translator, analyzer)
- LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST — optional Langfuse observability credentials
- MAX_FILE_SIZE_MB — maximum upload size (default 20)
- ALLOWED_EXTENSIONS — file types allowed (default: pdf,docx,txt,png,jpg,jpeg)

Example `.env` (create `backend/.env`):

```ini
APP_NAME=ContentLens_AI
ENV=development
LOG_LEVEL=INFO
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_EXTRACTOR=llama3.1
OLLAMA_MODEL_ROUTER=mistral
OLLAMA_MODEL_SUMMARIZER=llama3.1
OLLAMA_MODEL_TRANSLATOR=mistral
OLLAMA_MODEL_ANALYZER=llama3.1
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
MAX_FILE_SIZE_MB=20
ALLOWED_EXTENSIONS=pdf,docx,txt,png,jpg,jpeg
```

---

## 🔧 API Endpoints

Base route: `/api`

- POST `/api/process-document` — Uploads a file and a `user_request` form value (intent) to run the workflow. Responds with structured analysis JSON.

Example using `curl`:

```bash
curl -X POST "http://localhost:8000/api/process-document" \
  -F "file=@/path/to/document.pdf" \
  -F "user_request=Summarize the main points and extract action items"
```

Response: JSON matching `backend/app/api/schemas.py` (summary, extraction, language, metadata, etc.).

---

## 📁 Project Structure

Top-level overview:

- backend/ — Python FastAPI application
  - app/ — application package
    - api/ — API routes and request/response schemas
    - agents/ — modules for analyzer, extractor, summarizer, translator, router
    - core/ — configuration and logging
    - graphs/ — document graph and workflow state
    - tools/ — file loaders, OCR handling, language helpers, validators
    - workflows/ — main workflow orchestrations (process_document)
  - tests/ — pytest tests for API, agents and graphs

- frontend/ — React TypeScript client
  - src/ — core frontend code (components, pages, services)

- Makefile — common commands (where applicable)
- README.md — you are here

---

## 🧭 Usage Examples

- Basic: Upload a PDF containing meeting notes and ask: "Extract action items and summarize decisions." The backend will run the workflow and return a structured summary and extraction object.

- OCR: Upload a scanned image containing text — the OCR tool will attempt recognition and feed text to the extraction pipeline.

- Translation: Use the `user_request` to ask for translations or localized summaries, e.g., "Translate the summary to Spanish and give a short executive summary."

---

## 🤝 Contributing

Contributions are welcome! A suggested workflow:

1. Fork the repository and create a feature branch.
2. Open a pull request with a clear description of changes.
3. Add tests for new functionality and ensure existing tests pass.
4. Keep code style consistent — use meaningful commit messages.

**Responsible use note:** Please respect the project's intended use — features that support **responsible marketing workflows** (content generation, summarization, campaign research) are welcome, but they must include safeguards for consent, anti-spam measures, and privacy compliance. Avoid building features that enable unsolicited outreach or deceptive targeting.

If you'd like to propose a larger design or road-map change, please open an issue first so we can discuss the approach.

---

## 👤 Author / Contact

- Repository owner: **Ziadashraf301** (GitHub)
- For issues or questions, please open an issue in the repository or contact via GitHub profile: https://github.com/Ziadashraf301

---

## 💡 Notes & Tips

- Tesseract OCR: on Windows install the Tesseract binary and ensure `tesseract.exe` is in your PATH; on macOS use `brew install tesseract`.
- LLM runtime: The project assumes you have access to an Ollama instance or equivalent LLM endpoint. Adjust `OLLAMA_BASE_URL` and model names in `.env` accordingly.
- Security: For production deployments, secure your API and avoid using wildcard CORS origins.

---