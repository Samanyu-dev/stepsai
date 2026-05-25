from pydantic import BaseModel, Field
from typing import List, Optional

class ResumeProfile(BaseModel):
    """
    Pydantic schema representing the structured data extracted from a candidate's resume.
    Ensures validated fields are delivered end-to-end to guide mock interview questions.
    """
    candidate_name: Optional[str] = Field(
        default=None, 
        description="The full name of the candidate, if identifiable."
    )
    email: Optional[str] = Field(
        default=None, 
        description="Candidate's primary contact email address."
    )
    phone: Optional[str] = Field(
        default=None, 
        description="Contact phone number of the candidate."
    )
    linkedin: Optional[str] = Field(
        default=None, 
        description="LinkedIn profile URL if found on the resume."
    )
    github: Optional[str] = Field(
        default=None, 
        description="GitHub repository profile URL if present."
    )
    estimated_job_role: str = Field(
        ..., 
        description="Calculated primary job title target (e.g. Backend Engineer, Data Scientist, Frontend Developer)."
    )
    experience_level: str = Field(
        ..., 
        description="Calculated career seniority level based on work duration (e.g. Intern, Junior, Mid-level, Senior, Lead)."
    )
    skills: List[str] = Field(
        default_factory=list, 
        description="Detailed list of technical skills, frameworks, and programming languages extracted."
    )
    work_experience_summaries: List[str] = Field(
        default_factory=list, 
        description="Bullet summaries of past employment, roles, and major projects."
    )
    education_summaries: List[str] = Field(
        default_factory=list, 
        description="Acquired degrees, university programs, academic titles, or relevant training certifications."
    )
    key_strengths: List[str] = Field(
        default_factory=list, 
        description="Key highlights, unique expertise, or standout professional traits identified on the resume."
    )
