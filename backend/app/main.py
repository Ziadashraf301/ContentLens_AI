from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import (ApplicationException, 
                               application_exception_handler, 
                               global_exception_handler)
from app.api.routes.v1 import chat, documents

# Setup structured logging before app starts
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    version="1.0.0",
)

# CORS Middleware - restrict in production via settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(ApplicationException, application_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# API Routers
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat"])
app.include_router(documents.router, prefix=f"{settings.API_V1_STR}/documents", tags=["Documents"])


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}
