"""
Steps AI Mock Interview Evaluation Flow Tests.

This module asserts the correct operations of transcripts parser, overall scores
normalizations, circular metrics compilation, and FPDF PDF caches signatures.
"""

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.models.resume import ResumeProfile
from app.models.interview import Message, InterviewMode, DifficultyLevel
from app.services.interview_engine import interview_engine, resume_store
from app.services.evaluation import report_store

client = TestClient(app)

# Mock parsed Resume Profile
mock_profile = ResumeProfile(
    candidate_name="Alice Smith",
    email="alice@smith.com",
    phone="555-0100",
    estimated_job_role="Frontend Engineer",
    experience_level="Junior",
    skills=["HTML", "CSS", "React"],
    work_experience_summaries=["Intern Developer at Vance Refrigeration"],
    education_summaries=["Degree in Web Development"],
    key_strengths=["Pixel-perfect mockups"]
)

def test_end_interview_session_not_found():
    """
    Asserts that ending and evaluating a non-existent session ID returns a 404.
    """
    response = client.post(
        "/api/v1/interview/end",
        json={"session_id": "non-existent-uuid"}
    )
    assert response.status_code == 404
    assert "session does not exist" in response.json()["detail"]

@patch("app.services.evaluation.llm_service.client.chat.completions.create")
def test_evaluation_and_pdf_generation_flow(mock_groq):
    """
    Asserts that POST /interview/end processes the conversation transcript,
    calls Groq JSON Mode, maps evaluations, builds the PDF, and GET /report/{id} downloads it.
    """
    # 1. Boot up a mock interview session and add QA dialogue turns
    resume_session_id = resume_store.save_profile(mock_profile)
    session = interview_engine.store.create_session(
        resume_session_id=resume_session_id,
        interview_mode=InterviewMode.TECHNICAL,
        difficulty_level=DifficultyLevel.JUNIOR,
        total_questions=3,
        resume_profile=mock_profile
    )
    
    # Simulate a 1-turn conversation transcript inside session messages history
    session.messages.append(Message(role="assistant", content="What is your experience with React?"))
    session.messages.append(Message(role="user", content="I built responsive interfaces using hooks and components."))
    interview_engine.store.save_session(session)
    
    # 2. Mock Groq Chat Completions return payload JSON
    mock_choice = MagicMock()
    mock_choice.message.content = (
        "{\n"
        "  \"overall_score\": 75,\n"
        "  \"strengths\": [\"Comfortable with hooks\", \"Understand components\"],\n"
        "  \"weaknesses\": [\"Missing state management details\"],\n"
        "  \"summary_feedback\": \"Solid React basics, but needs deeper state management knowledge.\",\n"
        "  \"evaluations\": [\n"
        "    {\n"
        "      \"question\": \"What is your experience with React?\",\n"
        "      \"answer\": \"I built responsive interfaces using hooks and components.\",\n"
        "      \"clarity_score\": 8,\n"
        "      \"depth_score\": 6,\n"
        "      \"relevance_score\": 9,\n"
        "      \"confidence_score\": 7,\n"
        "      \"missing_concepts\": [\"Redux\", \"Context API\", \"performance optimization\"],\n"
        "      \"improvement_tips\": [\"Study state management options\", \"Mention virtual DOM concepts\"]\n"
        "    }\n"
        "  ]\n"
        "}"
    )
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_groq.return_value = mock_response
    
    # 3. Fire /interview/end
    end_payload = {"session_id": session.interview_session_id}
    response = client.post("/api/v1/interview/end", json=end_payload)
    
    assert response.status_code == 200
    report_data = response.json()
    assert report_data["session_id"] == session.interview_session_id
    assert report_data["overall_score"] == 75
    assert len(report_data["evaluations"]) == 1
    assert "Redux" in report_data["evaluations"][0]["missing_concepts"]
    
    # 4. Fire /report/{session_id} GET to download PDF
    report_url = f"/api/v1/report/{session.interview_session_id}"
    pdf_response = client.get(report_url)
    
    assert pdf_response.status_code == 200
    assert "application/pdf" in pdf_response.headers["content-type"]
    assert "attachment" in pdf_response.headers["content-disposition"]
    
    # Verify PDF standard header bytes Signature (%PDF)
    pdf_content = pdf_response.content
    assert pdf_content.startswith(b"%PDF")

def test_download_report_not_found():
    """
    Asserts that downloading a report PDF before compiling it returns a 404.
    """
    response = client.get("/api/v1/report/some-dummy-id")
    assert response.status_code == 404
    assert "PDF report was not found" in response.json()["detail"]
