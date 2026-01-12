from fastapi import FastAPI
from .api.routes import router as api_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ContentLens AI - Backend")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {"message": "ContentLens AI backend is running"}
