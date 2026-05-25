from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.models.resume import ResumeProfile

client = TestClient(app)

def test_upload_resume_invalid_format():
    """
    Assert that the resume upload API returns a 400 bad request 
    when the uploaded file is not a PDF.
    """
    response = client.post(
        "/api/v1/resume/upload",
        files={"file": ("resume.txt", b"Mock non-pdf content", "text/plain")}
    )
    assert response.status_code == 400
    assert "PDF format" in response.json()["detail"]

@patch("app.api.v1.resume.extract_text_from_pdf")
@patch("app.api.v1.resume.llm_service.parse_resume")
def test_upload_resume_success(mock_parse, mock_extract):
    """
    Assert that a successful PDF upload drives PyMuPDF text decoding
    and Anthropic Claude profile synthesis correctly.
    """
    # 1. Mock PyMuPDF extraction returning raw string
    mock_extract.return_value = "Jane Doe \n Software Engineer \n skills: Python, Go"
    
    # 2. Mock LLM Service returning validated ResumeProfile
    mock_profile = ResumeProfile(
        candidate_name="Jane Doe",
        email="jane.doe@example.com",
        phone="555-0199",
        linkedin="https://linkedin.com/in/janedoe",
        github="https://github.com/janedoe",
        estimated_job_role="Backend Developer",
        experience_level="Senior",
        skills=["Python", "Go", "FastAPI", "SQL"],
        work_experience_summaries=["Senior Developer at Techcorp (3 years)"],
        education_summaries=["B.Sc. in Computer Science"],
        key_strengths=["System Design", "Highly Scalable APIs"]
    )
    mock_parse.return_value = mock_profile
    
    # 3. Trigger mock POST request
    response = client.post(
        "/api/v1/resume/upload",
        files={"file": ("resume.pdf", b"%PDF-1.4 dummy binary content", "application/pdf")}
    )
    
    # 4. Assert responses
    assert response.status_code == 200
    
    data = response.json()
    assert data["candidate_name"] == "Jane Doe"
    assert data["estimated_job_role"] == "Backend Developer"
    assert data["experience_level"] == "Senior"
    assert "Go" in data["skills"]
    assert "System Design" in data["key_strengths"]
    
    # Verify exact call structures
    mock_extract.assert_called_once()
    mock_parse.assert_called_once_with("Jane Doe \n Software Engineer \n skills: Python, Go")
