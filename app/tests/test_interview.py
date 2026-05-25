"""
Steps AI Mock Interview Conversational Flow Tests.

This module asserts the correct operations of start parameters, difficulty auto-detection,
Server-Sent Events streaming chunks, question deduplication, and status retrieval.
"""

from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.models.resume import ResumeProfile
from app.services.interview_engine import interview_engine, resume_store

client = TestClient(app)

# Helper mock profile details
mock_profile = ResumeProfile(
    candidate_name="Bob Vance",
    email="bob@vance.com",
    phone="555-0199",
    linkedin="https://linkedin.com/in/bob",
    github="https://github.com/bob",
    estimated_job_role="Backend Developer",
    experience_level="Senior", # Senior level will trigger SENIOR difficulty auto-detection
    skills=["Python", "FastAPI", "PostgreSQL"],
    work_experience_summaries=["Backend Developer at Vance Refrigeration"],
    education_summaries=["B.Sc. in Refrigeration Science"],
    key_strengths=["MVCC optimizations"]
)

def test_start_interview_invalid_resume_session():
    """
    Asserts that starting an interview session with an invalid resume ID returns a 404.
    """
    response = client.post(
        "/api/v1/interview/start",
        json={
            "resume_session_id": "non-existent-uuid",
            "interview_mode": "Technical",
            "total_questions": 5
        }
    )
    assert response.status_code == 404
    assert "Resume session profile not found" in response.json()["detail"]

@patch("app.services.interview_engine.llm_service.chat_interview_question_stream")
@patch("app.services.interview_engine.llm_service.chat_interview_question_sync")
def test_interview_conversational_and_streaming_flow(mock_sync, mock_stream):
    """
    Asserts that the conversational engine starts cleanly, yields Server-Sent Events (SSE)
    tokens during answer progressions, and shuts down properly on final boundaries.
    """
    # Pre-populate resume store to mock a valid upload session
    resume_session_id = resume_store.save_profile(mock_profile)
    
    # 1. Mock Q1 Sync start opening
    mock_sync.return_value = "Hello Bob! Welcome. Can you describe your past projects?"
    
    start_payload = {
        "resume_session_id": resume_session_id,
        "interview_mode": "Technical",
        "total_questions": 3 # Configure a 3-question session
    }
    
    response = client.post("/api/v1/interview/start", json=start_payload)
    assert response.status_code == 200
    
    start_data = response.json()
    assert "interview_session_id" in start_data
    interview_session_id = start_data["interview_session_id"]
    assert start_data["first_question"] == "Hello Bob! Welcome. Can you describe your past projects?"
    assert start_data["difficulty_level"] == "Senior" # Confirms auto-detection mapped Senior experience level
    
    # 2. Answer Q1 -> streams Q2 chunks via SSE
    # Mock stream to yield token chunks
    mock_stream.return_value = ["Great ", "details. ", "How do ", "you handle ", "PostgreSQL ", "locks?"]
    
    answer_payload = {
        "session_id": interview_session_id,
        "answer": "I worked on MVCC optimizations and async drivers."
    }
    
    response = client.post("/api/v1/interview/answer", json=answer_payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    
    # Read the streamed SSE formatted lines
    sse_lines = response.text.split("\n")
    cleaned_sse_tokens = [line[6:] for line in sse_lines if line.startswith("data:")]
    assert "".join(cleaned_sse_tokens) == "Great details. How do you handle PostgreSQL locks?"

    # 3. Answer Q2 -> streams Q3 chunks via SSE
    mock_stream.return_value = ["Awesome! ", "Can you ", "write a ", "FastAPI ", "middleware?"]
    
    answer_payload = {
        "session_id": interview_session_id,
        "answer": "We avoid locks by choosing row-level locks only."
    }
    
    response = client.post("/api/v1/interview/answer", json=answer_payload)
    assert response.status_code == 200
    sse_lines = response.text.split("\n")
    cleaned_sse_tokens = [line[6:] for line in sse_lines if line.startswith("data:")]
    assert "".join(cleaned_sse_tokens) == "Awesome! Can you write a FastAPI middleware?"

    # 4. Answer Q3 (final allocated question) -> streams final concluding mock remark
    mock_stream.return_value = ["Thank you ", "Bob! That ", "concludes our ", "mock interview."]
    
    answer_payload = {
        "session_id": interview_session_id,
        "answer": "Yes, I inherit from BaseHTTPMiddleware."
    }
    
    response = client.post("/api/v1/interview/answer", json=answer_payload)
    assert response.status_code == 200
    sse_lines = response.text.split("\n")
    cleaned_sse_tokens = [line[6:] for line in sse_lines if line.startswith("data:")]
    assert "".join(cleaned_sse_tokens) == "Thank you Bob! That concludes our mock interview."

    # 5. Assert closed session error response on post-complete queries
    response = client.post("/api/v1/interview/answer", json=answer_payload)
    assert response.status_code == 400
    assert "already completed" in response.json()["detail"]

@patch("app.services.interview_engine.llm_service.chat_interview_question_stream")
@patch("app.services.interview_engine.llm_service.chat_interview_question_sync")
def test_interview_question_deduplication_flow(mock_sync, mock_stream):
    """
    Asserts that asked_questions list tracks newly generated questions
    and grows programmatically with each turn without duplicates.
    """
    resume_session_id = resume_store.save_profile(mock_profile)
    
    # Q1 opening question
    mock_sync.return_value = "Question 1: Describe your background."
    
    start_payload = {
        "resume_session_id": resume_session_id,
        "interview_mode": "Technical",
        "total_questions": 3
    }
    
    response = client.post("/api/v1/interview/start", json=start_payload)
    assert response.status_code == 200
    start_data = response.json()
    interview_session_id = start_data["interview_session_id"]
    
    # Verify asked_questions in session contains Q1
    session = interview_engine.store.get_session(interview_session_id)
    assert session is not None
    assert len(session.asked_questions) == 1
    assert session.asked_questions[0] == "Question 1: Describe your background."
    
    # Q2 question stream
    mock_stream.return_value = ["Question 2: What is FastAPI?"]
    answer_payload = {
        "session_id": interview_session_id,
        "answer": "I have experience with Python web frameworks."
    }
    response = client.post("/api/v1/interview/answer", json=answer_payload)
    assert response.status_code == 200
    
    # Verify asked_questions list grew to 2
    session = interview_engine.store.get_session(interview_session_id)
    assert session is not None
    assert len(session.asked_questions) == 2
    assert session.asked_questions[1] == "Question 2: What is FastAPI?"
    
    # Q3 question stream
    mock_stream.return_value = ["Question 3: How do you optimize SQLite?"]
    answer_payload = {
        "session_id": interview_session_id,
        "answer": "I use indexes and connections pooling."
    }
    response = client.post("/api/v1/interview/answer", json=answer_payload)
    assert response.status_code == 200
    
    # Verify asked_questions list grew to 3 and has no duplicates
    session = interview_engine.store.get_session(interview_session_id)
    assert session is not None
    assert len(session.asked_questions) == 3
    assert session.asked_questions[2] == "Question 3: How do you optimize SQLite?"
    assert len(set(session.asked_questions)) == 3

@patch("app.services.interview_engine.llm_service.chat_interview_question_sync")
def test_interview_session_status_endpoint(mock_sync):
    """
    Asserts that GET /api/v1/interview/status/{session_id} returns 200,
    contains all 7 status fields, and registers is_complete as False.
    """
    resume_session_id = resume_store.save_profile(mock_profile)
    mock_sync.return_value = "Question 1: Hello!"
    
    start_payload = {
        "resume_session_id": resume_session_id,
        "interview_mode": "Technical",
        "total_questions": 5
    }
    
    response = client.post("/api/v1/interview/start", json=start_payload)
    assert response.status_code == 200
    session_id = response.json()["interview_session_id"]
    
    # Fire status check
    status_response = client.get(f"/api/v1/interview/status/{session_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    
    # Assert contains all 7 fields
    assert "session_id" in status_data
    assert "question_count" in status_data
    assert "total_questions" in status_data
    assert "current_difficulty" in status_data
    assert "interview_mode" in status_data
    assert "elapsed_seconds" in status_data
    assert "is_complete" in status_data
    
    # Assert values
    assert status_data["session_id"] == session_id
    assert status_data["question_count"] == 1
    assert status_data["total_questions"] == 5
    assert status_data["interview_mode"] == "Technical"
    assert status_data["is_complete"] is False
    assert status_data["elapsed_seconds"] >= 0
