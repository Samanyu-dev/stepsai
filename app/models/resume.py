"""
Steps AI Resume Data Models.

This module defines Pydantic schemas representing the structured data profile
extracted from a candidate's resume by LLM parsing and taxonomy helpers.
"""

from pydantic import BaseModel, Field
from typing import List, Optional

class ResumeProfile(BaseModel):
    """
    Pydantic schema representing the structured data extracted from a candidate's resume.
    Ensures validated fields are delivered end-to-end to guide mock interview questions.
    """
    # Unified strict schema fields requested by the user
    name: Optional[str] = Field(default=None, description="Candidate full name.")
    job_role: Optional[str] = Field(default=None, description="Target job role (3 words max).")
    experience_years: int = Field(default=0, description="Estimated years of experience.")
    seniority: str = Field(default="Junior", description="Calculated seniority (Junior|Mid|Senior).")
    education: Optional[str] = Field(default=None, description="Highest degree acquired (5 words max).")
    summary: Optional[str] = Field(default=None, description="Profile summary (2 sentences max).")
    skill_gap_analysis: List[str] = Field(default_factory=list, description="Calculated missing core skills compared to target taxonomy.")

    # Backward-compatible fields for frontend representation
    candidate_name: Optional[str] = Field(default=None, description="Full name of candidate.")
    email: Optional[str] = Field(default=None, description="E-mail address.")
    phone: Optional[str] = Field(default=None, description="Contact phone number.")
    linkedin: Optional[str] = Field(default=None, description="LinkedIn profile URL.")
    github: Optional[str] = Field(default=None, description="GitHub profile URL.")
    estimated_job_role: str = Field(default="Software Engineer", description="Target engineering role.")
    experience_level: str = Field(default="Junior", description="Calculated seniority.")
    skills: List[str] = Field(default_factory=list, description="Extracted tech skills list.")
    work_experience_summaries: List[str] = Field(default_factory=list, description="Bullet summaries of past employment.")
    education_summaries: List[str] = Field(default_factory=list, description="Acquired academic degrees.")
    key_strengths: List[str] = Field(default_factory=list, description="Standout professional strengths.")
