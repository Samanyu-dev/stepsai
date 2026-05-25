from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.resume import ResumeProfile
from app.services.resume_parser import extract_text_from_pdf
from app.services.llm import llm_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload", response_model=ResumeProfile, tags=["Resume Intelligence"])
async def upload_resume(file: UploadFile = File(..., description="PDF file containing the candidate resume")):
    """
    Upload a resume PDF, parse the document text layers using PyMuPDF, and process the raw text
    using Anthropic Claude 3.5 Sonnet to compile a structured, validated profile schema.
    
    Returns:
        ResumeProfile: Structured data representing candidate skills, roles, experience, and education.
    """
    # Restrict uploads to PDF file types
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Please upload a valid document in PDF format (.pdf)."
        )
        
    try:
        # Read the binary stream of the uploaded file
        pdf_bytes = await file.read()
        
        # Stage 1: Parse the raw text layout out of the PDF structure
        resume_text = extract_text_from_pdf(pdf_bytes)
        
        # Stage 2: Profile parsed text into schema boundaries via Generative LLM tool calls
        profile = llm_service.parse_resume(resume_text)
        
        return profile
        
    except HTTPException as he:
        # Re-raise known API route exceptions
        raise he
    except Exception as e:
        logger.error(f"Unexpected crash inside upload_resume endpoint context: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected operational error occurred while profiling the resume: {str(e)}"
        )
