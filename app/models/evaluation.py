from pydantic import BaseModel, Field
from typing import List, Optional

class AnswerEvaluation(BaseModel):
    """
    Detailed evaluation grades and keyword gap analysis for a single interview question.
    """
    question: str = Field(..., description="The interview question asked by the recruiter.")
    answer: str = Field(..., description="The candidate's text answer.")
    clarity_score: int = Field(..., ge=0, le=10, description="Score for communication clarity (0-10).")
    depth_score: int = Field(..., ge=0, le=10, description="Score for technical depth and detail (0-10).")
    relevance_score: int = Field(..., ge=0, le=10, description="Score for contextual relevance to the question (0-10).")
    confidence_score: int = Field(..., ge=0, le=10, description="Estimated confidence level in the candidate response (0-10).")
    missing_concepts: List[str] = Field(default_factory=list, description="Important technical keywords or concepts omitted in the answer.")
    improvement_tips: List[str] = Field(default_factory=list, description="2-3 specific coaching tips to enhance this specific response.")

class FeedbackReport(BaseModel):
    """
    Overall consolidated performance assessment card for the mock interview session.
    """
    session_id: str = Field(..., description="The binding active mock interview session ID.")
    estimated_job_role: str = Field(..., description="The engineering or professional job role targeted.")
    experience_level: str = Field(..., description="Target seniority tier of the interview.")
    overall_score: int = Field(..., ge=0, le=100, description="Consolidated overall score out of 100.")
    strengths: List[str] = Field(default_factory=list, description="Top positive areas observed across the interview.")
    weaknesses: List[str] = Field(default_factory=list, description="Key operational gap areas or weaknesses.")
    summary_feedback: str = Field(..., description="Empathetic, comprehensive recruiter summary statement.")
    evaluations: List[AnswerEvaluation] = Field(default_factory=list, description="Individual breakdown evaluations per question.")
