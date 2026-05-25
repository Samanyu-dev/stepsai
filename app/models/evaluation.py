"""
Steps AI Performance Evaluation & Branded PDF Models.

This module defines Pydantic schemas representing the granular metrics, scorecards,
and consolidated performance diagnostic feedback reports generated after a session ends.
"""

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
    
    # Original overall metrics (backward-compatible with frontend UI)
    overall_score: int = Field(..., ge=0, le=100, description="Consolidated overall score out of 100.")
    strengths: List[str] = Field(default_factory=list, description="Top positive areas observed across the interview.")
    weaknesses: List[str] = Field(default_factory=list, description="Key operational gap areas or weaknesses.")
    summary_feedback: str = Field(..., description="Empathetic, comprehensive recruiter summary statement.")
    evaluations: List[AnswerEvaluation] = Field(default_factory=list, description="Individual breakdown evaluations per question.")
    
    # New strict evaluation scorecard metrics
    grade: str = Field(default="C", description="Hiring grade assigned (A|B|C|D|F).")
    hire_recommendation: str = Field(default="Maybe", description="Hiring recommendation decision (Strong Yes|Yes|Maybe|No).")
    technical_accuracy_score: int = Field(default=5, ge=0, le=10, description="Technical accuracy metric (0-10).")
    technical_accuracy_note: str = Field(default="", description="Technical accuracy assessment note.")
    communication_clarity_score: int = Field(default=5, ge=0, le=10, description="Communication clarity metric (0-10).")
    communication_clarity_note: str = Field(default="", description="Communication clarity assessment note.")
    problem_solving_score: int = Field(default=5, ge=0, le=10, description="Problem solving metric (0-10).")
    problem_solving_note: str = Field(default="", description="Problem solving assessment note.")
    depth_of_knowledge_score: int = Field(default=5, ge=0, le=10, description="Depth of knowledge metric (0-10).")
    depth_of_knowledge_note: str = Field(default="", description="Depth of knowledge assessment note.")
    confidence_score: int = Field(default=5, ge=0, le=10, description="Confidence metric (0-10).")
    confidence_note: str = Field(default="", description="Confidence assessment note.")
    missing_keywords: List[str] = Field(default_factory=list, description="Important technical terms never mentioned by candidate.")
    improvement_tips: List[str] = Field(default_factory=list, description="Actionable improvement suggestions.")
    benchmark_comparisons: str = Field(default="", description="Benchmarking comparisons with average candidate pool scores.")

