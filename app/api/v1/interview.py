from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.interview import (
    StartInterviewRequest,
    StartInterviewResponse,
    SubmitAnswerRequest
)
from app.services.interview_engine import interview_engine
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/start", response_model=StartInterviewResponse, tags=["Mock Interview Session"])
def start_interview(payload: StartInterviewRequest):
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

@router.post("/answer", tags=["Mock Interview Session"])
def submit_answer(payload: SubmitAnswerRequest):
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
