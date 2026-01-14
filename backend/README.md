# Backend — ContentLens AI (FastAPI)

This directory contains the FastAPI backend for ContentLens AI — a document analysis system designed to help marketing and product teams extract, summarize, translate, and analyze content from uploaded documents to accelerate content creation and research.

**Important:** The backend and the ContentLens project may be used to support **responsible marketing workflows** such as content ideation, summarization, and marketing asset generation. See the top-level README for guidance on consent, privacy, and ethical marketing practices.

---

## 🔧 Prerequisites
- Python 3.11+
- Tesseract OCR installed and available on PATH (optional, required for OCR features)
- Optional LLM runtime (e.g., Ollama) for local model execution

## Installation
1. Create and activate a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in `backend/` (see `backend/app/core/config.py` for available variables) and set values as needed.

Example `.env`:

```ini
APP_NAME=ContentLens_AI
ENV=development
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_EXTRACTOR=llama3.1
OLLAMA_MODEL_ROUTER=mistral
OLLAMA_MODEL_SUMMARIZER=llama3.1
MAX_FILE_SIZE_MB=20
ALLOWED_EXTENSIONS=pdf,docx,txt,png,jpg,jpeg
```

## Running (development)

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Open `http://localhost:8000/docs` for the automatic OpenAPI UI.

## API Summary
- POST `/api/process-document` — Upload a file (multipart form) and set `user_request` (intent) to run the workflow. See `backend/app/api/schemas.py` for response shape.

Example:

```bash
curl -X POST "http://localhost:8000/api/process-document" \
  -F "file=@/path/to/document.pdf" \
  -F "user_request=Summarize the main points and extract action items"
```

## Testing

Run backend tests with pytest:

```bash
pip install pytest
pytest backend/tests -q
```

## Troubleshooting & Tips
- If you need OCR, install Tesseract and ensure `tesseract` is accessible on the PATH.
- If you use local LLM runtimes, confirm `OLLAMA_BASE_URL` and model names are set in `.env`.
- Logs are configured in `backend/app/core/logging.py` and can be adjusted via `LOG_LEVEL`.

## Responsible Use & Security
- **Marketing usage (allowed with safeguards):** The backend can be used to support responsible marketing workflows (e.g., content generation, summaries, campaign research) provided you implement consent, opt-in, and anti-spam protections. Avoid using the system to send unsolicited outreach or to perform covert profiling, and ensure compliance with applicable laws and platform policies.
- **Data privacy:** Avoid uploading PII or sensitive data unless you have a lawful basis and safeguards in place.
- **Human review:** Treat outputs as suggestions — verify and validate results before using them in production or sharing.

---

## Marketing Agents Included
This project includes three initial marketing-focused agents that can be used in workflows:

- `IdeationAgent` — generates marketing campaign ideas and brief execution notes.
- `CopywriterAgent` — drafts multiple copy variants for emails, ads, and landing pages.
- `ComplianceAgent` — deterministic rule-based checks for privacy and marketing claim issues.

These agents are integrated into the document workflow and can be invoked when the Router decides the user's request requires marketing tasks. Additional agents (A/B testing, personalization, analytics) can be added later.

## Contributing
Contributions are welcome. Please follow the project's contributing guidelines in the top-level README and respect the responsible-use policies above.

---

## Contact
Open issues or reach out via the repository owner: https://github.com/Ziadashraf301
