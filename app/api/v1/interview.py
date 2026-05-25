"""
Steps AI Mock Interview Router.

This module exposes endpoints for launching sessions, checking session status,
submitting answer turns, and streaming recruiter responses back to the client.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.models.interview import (
    StartInterviewRequest,
    StartInterviewResponse,
    SubmitAnswerRequest,
    SessionStatusResponse
)
from app.core.db import get_db_connection
from datetime import datetime
from app.services.interview_engine import interview_engine
from app.core.rate_limiter import interview_limiter
from app.core.security import get_api_key
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/start", response_model=StartInterviewResponse, tags=["Mock Interview Session"], dependencies=[Depends(interview_limiter)])
def start_interview(payload: StartInterviewRequest, api_key: str = Depends(get_api_key)):
    """
    Launches a new mock interview conversation session using a previously uploaded resume session ID.
    Configures target recruiter modes and seniority difficulty levels.
    
    Returns:
        StartInterviewResponse: Metadata and opening recruiter question Q1.
    """
    try:
        session = interview_engine.start_interview(
            resume_session_id=payload.resume_session_id,
            interview_mode=payload.interview_mode,
            difficulty_level=payload.difficulty_level,
            total_questions=payload.total_questions
        )
        return StartInterviewResponse(
            interview_session_id=session.interview_session_id,
            resume_session_id=session.resume_session_id,
            first_question=session.messages[-1].content,
            interview_mode=session.interview_mode,
            difficulty_level=session.difficulty_level,
            total_questions=session.total_questions
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to start mock interview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while initializing mock interview: {str(e)}"
        )

@router.post("/answer", tags=["Mock Interview Session"], dependencies=[Depends(interview_limiter)])
def submit_answer(payload: SubmitAnswerRequest, api_key: str = Depends(get_api_key)):
    """
    Submits candidate's answer response to the active question turn.
    Streams back the recruiter follow-ups and next questions in real-time
    using Server-Sent Events (SSE) formatting.
    
    Returns:
        StreamingResponse: Stream of conversational token events (text/event-stream).
    """
    try:
        # Validate that session exists and is active before creating the stream context
        session = interview_engine.store.get_session(payload.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="The specified interview session does not exist.")
        if session.completed:
            raise HTTPException(status_code=400, detail="This mock interview session is already completed.")

        def sse_event_generator():
            try:
                # Yield recruiter tokens sequentially
                for token in interview_engine.progress_interview_stream(payload.session_id, payload.answer):
                    # Yield in standard Server-Sent Events formatting
                    yield f"data: {token}\n\n"
            except Exception as e:
                logger.error(f"Operational failure yielding interview SSE token stream: {str(e)}", exc_info=True)
                yield f"data: [STREAM_ERROR: {str(e)}]\n\n"

        return StreamingResponse(sse_event_generator(), media_type="text/event-stream")

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected operational failure inside submit_answer endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process answer stream: {str(e)}"
        )

@router.get("/status/{session_id}", response_model=SessionStatusResponse, tags=["Mock Interview Session"], dependencies=[Depends(interview_limiter)])
def get_session_status(session_id: str, api_key: str = Depends(get_api_key)):
    """
    Returns the current active state of a mock interview session.
    """
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM interviews WHERE interview_session_id = ?", (session_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="The specified interview session does not exist.")
        
        # Calculate elapsed seconds from created_at
        created_at_str = row["created_at"]
        
        # Parse created_at string
        try:
            created_at_dt = datetime.fromisoformat(created_at_str.replace(" ", "T"))
        except ValueError:
            created_at_dt = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
            
        elapsed = datetime.utcnow() - created_at_dt
        elapsed_seconds = max(0, int(elapsed.total_seconds()))
        
        return SessionStatusResponse(
            session_id=row["interview_session_id"],
            question_count=row["current_question_index"],
            total_questions=row["total_questions"],
            current_difficulty=row["difficulty_level"],
            interview_mode=row["interview_mode"],
            elapsed_seconds=elapsed_seconds,
            is_complete=bool(row["completed"])
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to fetch session status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while fetching session status: {str(e)}"
        )
    finally:
        conn.close()
