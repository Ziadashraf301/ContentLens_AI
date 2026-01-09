from fastapi import FastAPI
from .api.routes import router as api_router

app = FastAPI(title="ContentLens AI - Backend")

app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "ContentLens AI backend is running"}
