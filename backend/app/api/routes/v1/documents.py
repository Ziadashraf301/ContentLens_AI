from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException, status
from app.services.document_parser import DocumentParserService
from app.agents.doc_qa_agent import DocumentQAAgent
from app.models.schemas.responses.AnalysisResponse import AnalysisResponse
from app.api.dependencies.auth import get_current_user, UserContext
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter()
doc_qa_agent = DocumentQAAgent()

@router.post("/process-document", response_model=AnalysisResponse)
async def process_document(
    file: UploadFile = File(...),
    user_request: str = Form("Summarize this document"),
    current_user: UserContext = Depends(get_current_user)
):
    """
    Parse uploaded document (PDF, DOCX, TXT, Image OCR) and run QA or summary.
    """
    logger.info("Processing document request", 
                filename=file.filename, 
                user_id=current_user.user_id, 
                tenant_id=current_user.tenant_id)
    
    # Parse the document text
    extracted_text = await DocumentParserService.parse_file(file)
    if not extracted_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to extract text from the uploaded document."
        )

    try:
        # Run QA Agent to get analysis/summary
        answer = await doc_qa_agent.answer_question(extracted_text, user_request)
        
        # Build standard response
        return AnalysisResponse(
            raw_text=extracted_text,
            source_lang="en",
            summary=answer,
            analysis=f"Processed query: {user_request}",
            extraction={"filename": file.filename, "character_count": len(extracted_text)}
        )
    except Exception as e:
        logger.error("Error running QA agent on document", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating answer: {str(e)}"
        )
