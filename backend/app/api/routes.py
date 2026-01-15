import os
import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from ..workflows.process_document import run_document_workflow
from .schemas import AnalysisResponse, ScoreRequest
from ..core.logging import logger
from ..core.langfuse import get_langfuse_tracer

router = APIRouter()

@router.post("/process-document", response_model=AnalysisResponse)
async def process_document(
    file: UploadFile = File(...),
    user_request: str = Form("Analyze this document")
):
    """
    1. Receives file and user intent from Frontend.
    2. Saves file to a temporary location.
    3. Executes the LangGraph workflow.
    4. Cleans up and returns results.
    """
    
    # Create temp directory if not exists
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, file.filename)

    try:
        # Save file locally for processing
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"API: Received file {file.filename}. Request: {user_request}")

        # Trigger the full workflow
        result = await run_document_workflow(file_path, user_request)

        if "error" in result and not result.get("extraction"):
             raise HTTPException(status_code=500, detail=result["error"])

        return result

    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
    finally:
        # Cleanup the temp file after processing
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/score-agent")
async def score_agent(request: ScoreRequest):
    """
    Manually score an agent execution for evaluation.
    """
    try:
        tracer = get_langfuse_tracer()
        if not tracer.client:
            raise HTTPException(status_code=503, detail="Langfuse not configured")

        # Retrieve the trace by ID
        trace = tracer.client.get_trace(id=request.trace_id)
        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")

        # Add the score to the trace
        tracer.add_score(
            trace,
            name=f"{request.agent_name}_manual_score",
            value=request.score,
            comment=request.comment or "Manual user score"
        )

        logger.info(f"Scored agent {request.agent_name} with {request.score} for trace {request.trace_id}")
        return {"status": "score recorded", "trace_id": request.trace_id}

    except Exception as e:
        logger.error(f"Scoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))