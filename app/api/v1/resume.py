"""
Steps AI Resume Intelligence Router.

This module registers endpoints for uploading resumes (in PDF/DOCX formats),
size validation gating, rate limiting, and retrieving parsed resume profiles.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.models.resume import ResumeProfile
from app.services.resume_parser import extract_text_from_file
from app.services.llm import llm_service
from app.services.interview_engine import resume_store
from app.core.rate_limiter import upload_limiter
from app.core.security import get_api_key
from app.core.db import get_db_connection
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload", tags=["Resume Intelligence"], dependencies=[Depends(upload_limiter)])
async def upload_resume(
    file: UploadFile = File(..., description="PDF or Microsoft Word (.docx) resume file"),
    api_key: str = Depends(get_api_key)
):
    """
    Upload a resume (PDF or Word .docx document), decode raw text,
    trigger Groq Llama-3.3-70b JSON Mode parsing, and cache the compiled
    profile inside the persistent SQLite database.
    
    Returns:
        dict: Compiled session_id and structured ResumeProfile schema content.
    """
    try:
        # Enforce server-side file type validation
        filename = file.filename if file.filename else ""
        lower_filename = filename.lower()
        if not (lower_filename.endswith(".pdf") or lower_filename.endswith(".docx")):
            raise HTTPException(
                status_code=400,
                detail="Unsupported document format. Please upload a valid PDF (.pdf) or Microsoft Word (.docx) document."
            )

        # Read uploaded document binary data
        file_bytes = await file.read()
        
        # Enforce server-side file size validation (max 5 MB limit)
        max_size = 5 * 1024 * 1024
        if len(file_bytes) > max_size:
            raise HTTPException(
                status_code=413,
                detail="The uploaded file exceeds the maximum permitted size threshold of 5 MB."
            )
        
        # Stage 1: Decode text layers based on file extension
        raw_text = extract_text_from_file(file_bytes, filename)
        
        # Stage 2: Orchestrate Groq Llama-3.3 parsing with JSON mode validation
        profile = llm_service.parse_resume(raw_text)
        
        # Stage 3: Store parsed profile in SQLite DB mapping to session_id
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
def get_parsed_resume(session_id: str, api_key: str = Depends(get_api_key)):
    """
    Fetch a previously parsed candidate profile using its unique session ID.
    """
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM resumes WHERE session_id = ?", (session_id,)).fetchone()
        if not row:
            raise HTTPException(
                status_code=404,
                detail="The specified resume profile session ID was not found."
            )
        
        # Verify expiry (24 hours check)
        created_at_str = row["created_at"]
        try:
            created_at_dt = datetime.fromisoformat(created_at_str.replace(" ", "T"))
        except ValueError:
            created_at_dt = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
            
        if datetime.utcnow() - created_at_dt > timedelta(hours=24):
            raise HTTPException(
                status_code=410,
                detail="Resume session expired. Please re-upload."
            )
            
        profile_dict = json.loads(row["profile_json"])
        return ResumeProfile(**profile_dict)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to fetch parsed resume: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while fetching resume profile: {str(e)}"
        )
    finally:
        conn.close()
