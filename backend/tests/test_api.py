import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
import backend.app.api.routes as routes

client = TestClient(app)


def test_root():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json().get("message") == "ContentLens AI backend is running"


def test_process_document_success(monkeypatch, tmp_path):
    async def fake_run(file_path, user_request):
        return {"summary": "ok", "extraction": {"title": "t"}}

    monkeypatch.setattr(routes, "run_document_workflow", fake_run)

    file_content = b"Hello world"
    files = {"file": ("test.txt", file_content, "text/plain")}

    res = client.post("/api/process-document", files=files, data={"user_request": "Summarize"})
    assert res.status_code == 200
    j = res.json()
    assert "summary" in j and "extraction" in j


def test_process_document_failure(monkeypatch):
    async def fake_run(file_path, user_request):
        return {"error": "failed to extract"}

    monkeypatch.setattr(routes, "run_document_workflow", fake_run)

    files = {"file": ("test.txt", b"Hello", "text/plain")}
    res = client.post("/api/process-document", files=files)
    assert res.status_code == 500


def test_process_document_exception(monkeypatch):
    async def fake_run(file_path, user_request):
        raise Exception("boom")

    monkeypatch.setattr(routes, "run_document_workflow", fake_run)

    files = {"file": ("test.txt", b"Hello", "text/plain")}
    res = client.post("/api/process-document", files=files)
    assert res.status_code == 500
