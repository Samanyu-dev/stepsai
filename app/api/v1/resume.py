from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.resume import ResumeProfile
from app.services.resume_parser import extract_text_from_file
from app.services.llm import llm_service
from app.services.interview_engine import resume_store
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload", tags=["Resume Intelligence"])
async def upload_resume(file: UploadFile = File(..., description="PDF or Microsoft Word (.docx) resume file")):
    """
    Upload a resume (PDF or Word .docx document), decode raw text,
    trigger Groq Llama-3.3-70b JSON Mode parsing, and cache the compiled
    profile inside the volatile session dictionary.
    
    Returns:
        dict: Compiled session_id and structured ResumeProfile schema content.
    """
    try:
        # Read uploaded document binary data
        file_bytes = await file.read()
        
        # Stage 1: Decode text layers based on file extension
        raw_text = extract_text_from_file(file_bytes, file.filename)
        
        # Stage 2: Orchestrate Groq Llama-3.3 parsing with JSON mode validation
        profile = llm_service.parse_resume(raw_text)
        
        # Stage 3: Store parsed profile in volatile store mapping to session_id
        session_id = resume_store.save_profile(profile)
        
        return {
            "session_id": session_id,
            "profile": profile
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Uncaught exception inside resume upload route: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected operational failure occurred while profiling the resume: {str(e)}"
        )

@router.get("/{session_id}", response_model=ResumeProfile, tags=["Resume Intelligence"])
def get_parsed_resume(session_id: str):
    """
    Fetch a previously parsed candidate profile using its unique session ID.
    """
    profile = resume_store.get_profile(session_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="The specified resume profile session ID was not found."
        )
    return profile
