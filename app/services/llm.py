import logging
import json
from anthropic import Anthropic
from app.core.config import settings
from app.models.resume import ResumeProfile
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class LLMService:
    """
    Extensible LLM gateway wrapping Generative AI clients (principally Anthropic Claude 3.5 Sonnet)
    to perform deterministic parsing, multi-turn interviews, and scoring rubrics.
    """
    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.client = None
        
        # Initialize Anthropic SDK if active key is detected
        if self.api_key and self.api_key != "your-anthropic-api-key-here":
            self.client = Anthropic(api_key=self.api_key)
        else:
            logger.warning(
                "ANTHROPIC_API_KEY is not configured or uses default template. "
                "Generative LLM tasks will fail until a valid key is provided in the configuration."
            )

    def parse_resume(self, resume_text: str) -> ResumeProfile:
        """
        Parses un-structured resume text using Claude 3.5 Sonnet's Tool Use (Function Calling).
        Enforces output schema matching the validated ResumeProfile Pydantic representation.
        
        Args:
            resume_text (str): Raw extracted document text.
            
        Returns:
            ResumeProfile: Validated structured profile details.
        """
        if not self.client:
            logger.error("Claude client not initialized. ANTHROPIC_API_KEY environment variable is missing.")
            raise HTTPException(
                status_code=500,
                detail=(
                    "Anthropic integration is not configured. Please supply a valid "
                    "ANTHROPIC_API_KEY in your local environment configurations."
                )
            )

        # Define the structural schema representing the ResumeProfile data class
        tool_schema = {
            "name": "parse_resume",
            "description": "Analyze resume content to extract profile data fields.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "candidate_name": {
                        "type": "string",
                        "description": "Candidate's full name, if present on the document."
                    },
                    "email": {
                        "type": "string",
                        "description": "Identified contact email address."
                    },
                    "phone": {
                        "type": "string",
                        "description": "Found phone number."
                    },
                    "linkedin": {
                        "type": "string",
                        "description": "LinkedIn profile link URL."
                    },
                    "github": {
                        "type": "string",
                        "description": "GitHub profile link URL."
                    },
                    "estimated_job_role": {
                        "type": "string",
                        "description": "Primary estimated job role based on skills (e.g. Frontend Engineer, ML Engineer, Backend Developer)."
                    },
                    "experience_level": {
                        "type": "string",
                        "description": "Seniority tier based on depth/years of experience (e.g. Intern, Junior, Mid-level, Senior, Lead)."
                    },
                    "skills": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Detailed list of technical skills, frameworks, and programming languages."
                    },
                    "work_experience_summaries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Brief summaries highlighting past employment, job roles, and key projects."
                    },
                    "education_summaries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Education details, degrees, academic institutions, or certifications."
                    },
                    "key_strengths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Unique selling points, strengths, or prominent career landmarks."
                    }
                },
                "required": ["estimated_job_role", "experience_level", "skills"]
            }
        }

        try:
            # Direct Claude to parse the text and execute the structured parsing tool
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2500,
                temperature=0.0,  # Set temperature to 0.0 to ensure deterministic schemas and profiles
                system=(
                    "You are an elite talent acquisition AI parser and career strategist. "
                    "Analyze the provided resume document text, isolate contact structures, "
                    "compile all coding skills/frameworks, list chronological jobs, and assess "
                    "the candidate's exact experience tier based on responsibilities."
                ),
                messages=[
                    {
                        "role": "user",
                        "content": f"Please parse this resume text and populate the parse_resume schema:\n\n{resume_text}"
                    }
                ],
                tools=[tool_schema],
                tool_choice={"type": "tool", "name": "parse_resume"}
            )

            # Retrieve the structured tool block out of Claude response
            tool_use = next((content for content in response.content if content.type == "tool_use"), None)
            
            if not tool_use:
                raise HTTPException(
                    status_code=502,
                    detail="Generative LLM model did not execute the structured tool parser schema."
                )

            extracted_fields = tool_use.input
            
            # Map raw fields to validated Pydantic model
            return ResumeProfile(**extracted_fields)

        except Exception as e:
            logger.error(f"Failed to communicate with Anthropic REST endpoint: {str(e)}", exc_info=True)
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=502,
                detail=f"Upstream Generative AI service failed to parse the profile: {str(e)}"
            )

# Singleton service instance
llm_service = LLMService()
