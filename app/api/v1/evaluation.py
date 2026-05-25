from fastapi import APIRouter, Response, HTTPException
from app.models.evaluation import FeedbackReport
from app.services.evaluation import evaluation_service, report_store
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class EndInterviewRequest(BaseModel):
    session_id: str = Field(..., description="Unique UUID assigned to this interview session.")

@router.post("/interview/end", response_model=FeedbackReport, tags=["Evaluation & Feedback"])
def end_interview(payload: EndInterviewRequest):
    """
    Terminates the mock interview conversation session, extracts transcript logs,
    deploys Groq Llama-3.3 JSON scoring rules, and automatically compiles the premium PDF.
    
    Returns:
        FeedbackReport: Comprehensive JSON overview feedback profile with per-question breakdowns.
    """
    try:
        report = evaluation_service.evaluate_interview(payload.session_id)
        return report
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to end and evaluate mock interview session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected operational failure occurred during evaluations: {str(e)}"
        )

@router.get("/report/{session_id}", tags=["Evaluation & Feedback"])
def download_pdf_report(session_id: str):
    """
    Download the generated mock interview performance report card in a premium PDF layout.
    Requires calling POST /end first to generate the report structure.
    """
    # Retrieve PDF binary bytes out of volatile memory
    pdf_bytes = report_store.get_pdf(session_id)
    if not pdf_bytes:
        raise HTTPException(
            status_code=404,
            detail="The requested PDF report was not found. Please call POST /end first to compile it."
        )
        
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=stepsai_report_{session_id[:8]}.pdf"
        }
    )
