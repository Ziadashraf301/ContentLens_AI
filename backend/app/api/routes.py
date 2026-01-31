import os
import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from ..workflows.process_document import run_document_workflow
from ..models.schemas.ScoreRequest import ScoreRequest
from ..models.schemas.AnalysisResponse import AnalysisResponse
from ..core.logging import logger
from ..core.langfuse import get_langfuse_tracer
from langfuse import propagate_attributes

router = APIRouter()

@router.post("/process-document", response_model=AnalysisResponse)
async def process_document(
    file: UploadFile = File(...),
    user_request: str = Form("Analyze this document")
):
    """
    1. Receives file and user intent from Frontend.
    2. Saves file to a temporary location.
    3. Executes the LangGraph workflow with tracing.
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

        # START TRACER HERE
        tracer = get_langfuse_tracer()
        
        with propagate_attributes(tags=["api", "document_processing", "production"]):
            with tracer.client.start_as_current_observation(
                as_type="span",  # This is the root trace
                name="api_document_processing",
                input={
                    "filename": file.filename,
                    "user_request": user_request,
                    "file_size": file.size if hasattr(file, 'size') else 0
                },
                metadata={
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "endpoint": "/api/process-document"
                }
            ) as api_trace:
                
                # Trigger the workflow (pass the trace context)
                result = await run_document_workflow(file_path, user_request, tracer=tracer)

                if "error" in result and not result.get("extraction"):
                    api_trace.update_trace(
                        output={"error": result["error"], "status": "failed"}
                    )
                    api_trace.score(
                        name="api_success",
                        value=0.0,
                        comment=f"Workflow error: {result['error']}",
                        data_type="NUMERIC"
                    )
                    raise HTTPException(status_code=500, detail=result["error"])
                
                # Success - update trace
                api_trace.update_trace(
                    output={
                        "status": "success",
                        "trace_id": result.get("trace_id"),
                        "completed_steps": result.get("next_steps", [])
                    }
                )
                api_trace.score(
                    name="api_success",
                    value=1.0,
                    comment="API request completed successfully",
                    data_type="NUMERIC"
                )
                
                # Add the API trace ID to the result
                result["api_trace_id"] = api_trace.trace_id if hasattr(api_trace, 'trace_id') else None

                return result

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
        
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
        from ..core.langfuse import get_langfuse_client
        
        client = get_langfuse_client()
        if not client:
            raise HTTPException(status_code=503, detail="Langfuse not configured")

        # Get trace
        trace = client.api.trace.get(request.trace_id)
        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")

        # Add the score using create_score
        client.create_score(
            trace_id=request.trace_id,
            name=f"{request.agent_name}_manual_score",
            value=request.score,
            comment=request.comment or "Manual user score",
            data_type="NUMERIC"
        )

        logger.info(f"Scored agent {request.agent_name} with {request.score} for trace {request.trace_id}")
        return {"status": "score recorded", "trace_id": request.trace_id}

    except Exception as e:
        logger.error(f"Scoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))