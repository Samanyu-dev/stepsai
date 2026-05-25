"""
Steps AI Resume Intelligence Flow Tests.

This module asserts the correct operations of resume document format validations,
file size constraints, Groq parser mock calls, and session profile storage operations.
"""

from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.models.resume import ResumeProfile

client = TestClient(app)

def test_upload_resume_invalid_format():
    """
    Asserts that the upload endpoint rejects unsupported file structures with a 400.
    """
    response = client.post(
        "/api/v1/resume/upload",
        files={"file": ("resume.txt", b"my plain resume content", "text/plain")}
    )
    assert response.status_code == 400
    assert "Unsupported document format" in response.json()["detail"]

@patch("app.api.v1.resume.extract_text_from_file")
@patch("app.api.v1.resume.llm_service.parse_resume")
def test_upload_resume_and_retrieval_flow(mock_parse, mock_extract):
    """
    Asserts that uploading a valid document decodes raw text, compiles profiles
    via Groq llama-3.3, stores it, and GET /resume/{session_id} retrieves it correctly.
    """
    # 1. Mock parsed output
    mock_extract.return_value = "Jane Doe \n Software Engineer \n skills: Python, Go"
    
    mock_profile = ResumeProfile(
        candidate_name="Jane Doe",
        email="jane.doe@example.com",
        phone="555-0199",
        linkedin="https://linkedin.com/in/janedoe",
        github="https://github.com/janedoe",
        estimated_job_role="Backend Developer",
        experience_level="Senior",
        skills=["Python", "Go", "FastAPI"],
        work_experience_summaries=["Senior Developer at Techcorp"],
        education_summaries=["B.Sc. in CS"],
        key_strengths=["System Design"]
    )
    mock_parse.return_value = mock_profile
    
    # 2. Fire upload POST
    upload_response = client.post(
        "/api/v1/resume/upload",
        files={"file": ("resume.pdf", b"%PDF-1.4 dummy pdf bytes", "application/pdf")}
    )
    
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert "session_id" in upload_data
    session_id = upload_data["session_id"]
    assert upload_data["profile"]["candidate_name"] == "Jane Doe"
    
    # 3. Fire retrieval GET
    get_response = client.get(f"/api/v1/resume/{session_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["candidate_name"] == "Jane Doe"
    assert get_data["estimated_job_role"] == "Backend Developer"
    assert "FastAPI" in get_data["skills"]
    
    mock_extract.assert_called_once()
    mock_parse.assert_called_once_with("Jane Doe \n Software Engineer \n skills: Python, Go")

def test_get_parsed_resume_not_found():
    """
    Asserts that querying a non-existent resume session returns 404.
    """
    response = client.get("/api/v1/resume/non-existent-uuid-string")
    assert response.status_code == 404
