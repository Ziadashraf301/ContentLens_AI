# Frontend — ContentLens AI (React + TypeScript)

This directory contains the React + TypeScript frontend for ContentLens AI. The UI provides file upload, status, and result views for the backend document-processing workflows.

**Important:** The frontend is suitable to support **marketing workflows** such as uploading campaign documents, generating summaries, and producing marketing assets. When used for marketing purposes, ensure clear consent, data minimization, and opt-in flows to avoid unsolicited or abusive usage.

---

## Prerequisites
- Node.js 16+ and npm (or Yarn)

## Setup

```bash
cd frontend
npm install
# or
# yarn
```

## Environment
Set `REACT_APP_API_URL` to override the API base URL if needed. By default the frontend will use same-origin requests.

Examples:

```bash
# Run in development, pointing to local backend
# Windows PowerShell
$env:REACT_APP_API_URL = "http://localhost:8000"
npm start
```

## Run (development)

```bash
npm start
```

Open `http://localhost:3000` to use the UI.

## Marketing agent support
The frontend can be used to invoke marketing-oriented workflows by providing an appropriate `user_request` when uploading documents (e.g., "Generate campaign ideas and email subject lines"). Future UI improvements may add a dedicated "Marketing" workflow selector and approval UI for human review.

## Build (production)

```bash
npm run build
```

## Testing
Add frontend tests as needed (this project uses React Testing Library / Jest if present).

## Responsible Use & Privacy
- **Marketing usage (allowed with safeguards):** You may use the UI to support authorized marketing tasks (content creation, analysis, and asset generation) but implement safeguards for consent, privacy, and anti-spam protections. Do not use the UI to enable unsolicited messaging or deceptive profiling.
- **User consent:** Ensure any data collected from users is done with clear consent and in accordance with privacy regulations.

---

## Contributing
Contributions welcome — follow the top-level contributing guidance and respect responsible-use constraints.

---

## Contact
See repository owner: https://github.com/Ziadashraf301