"""
Steps AI Groq LLM Gateway Service.

This module houses the generative AI client for parsing resumes, streaming chat turns
token-by-token, and executing strict multi-dimensional scorecard JSON grading.
"""

import logging
import json
# pyrefly: ignore [missing-import]
from groq import Groq
from app.core.config import settings
from app.models.resume import ResumeProfile
from app.core.taxonomy import analyze_skill_gaps
from fastapi import HTTPException
from typing import Generator, List, Any

logger = logging.getLogger(__name__)

class LLMService:
    """
    Service gateway mapping generative AI pipelines (specifically Groq's llama-3.3-70b-versatile)
    to parse resume contents and stream conversational responses.
    """
    def __init__(self) -> None:
        self.api_key = settings.GROQ_API_KEY
        self.client = None
        
        # Initialize Groq client if active key is configured
        if self.api_key and self.api_key != "your-groq-api-key-here":
            self.client = Groq(api_key=self.api_key)
        else:
            logger.warning(
                "GROQ_API_KEY is not configured or uses default template. "
                "AI functionalities will fail until a valid key is bound."
            )

    def parse_resume(self, resume_text: str) -> ResumeProfile:
        """
        Parses document text using Groq llama-3.3-70b-versatile with JSON Mode
        to extract structured candidate details matching the exact requested prompt structure.
        """
        if not self.client:
            logger.error("Groq client not initialized. GROQ_API_KEY environment variable is missing.")
            raise HTTPException(
                status_code=500,
                detail="Groq integration is not configured. Please supply a valid GROQ_API_KEY."
            )

        # Exact parser prompt specified by the user
        system_prompt = (
            "Extract structured data from this resume text. Return ONLY valid JSON, no markdown, no explanation.\n\n"
            "Return this exact structure:\n"
            "{\n"
            "  \"name\": \"string\",\n"
            "  \"email\": \"string or null\",\n"
            "  \"phone\": \"string or null\", \n"
            "  \"job_role\": \"most likely target role in 3 words max\",\n"
            "  \"experience_years\": number,\n"
            "  \"seniority\": \"Junior|Mid|Senior\",\n"
            "  \"skills\": [\"skill1\", \"skill2\"],\n"
            "  \"education\": \"highest degree in 5 words max\",\n"
            "  \"summary\": \"candidate profile in 2 sentences max\"\n"
            "}\n\n"
            "Rules:\n"
            "- experience_years: 0 if fresher, estimate from dates if not stated\n"
            "- seniority: Junior=0-2yr, Mid=2-5yr, Senior=5+yr\n"
            "- skills: max 15, only hard skills\n"
            "- null for missing fields, never omit keys"
        )

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
                temperature=0.1,      # Deterministic extraction
                max_tokens=800,       # Strict ceiling
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Resume:\n{resume_text}"}
                ]
            )

            raw_json = response.choices[0].message.content
            if not raw_json:
                raise HTTPException(
                    status_code=502,
                    detail="Generative AI parsing gateway returned empty response content."
                )
            parsed_dict = json.loads(raw_json)
            
            # Programmatically calculate skill gaps compared to role taxonomy
            candidate_skills = parsed_dict.get("skills", [])
            candidate_role = parsed_dict.get("job_role", "Software Engineer")
            gaps = analyze_skill_gaps(candidate_role, candidate_skills)
            
            # Build unified Pydantic profile populating both new and backward-compatible fields
            return ResumeProfile(
                name=parsed_dict.get("name"),
                job_role=candidate_role,
                experience_years=int(parsed_dict.get("experience_years", 0)),
                seniority=parsed_dict.get("seniority", "Junior"),
                education=parsed_dict.get("education"),
                summary=parsed_dict.get("summary"),
                skill_gap_analysis=gaps,
                
                # Back-compat fields for SPA Frontend
                candidate_name=parsed_dict.get("name"),
                email=parsed_dict.get("email"),
                phone=parsed_dict.get("phone"),
                estimated_job_role=candidate_role,
                experience_level=parsed_dict.get("seniority", "Junior"),
                skills=candidate_skills,
                work_experience_summaries=[parsed_dict.get("summary", "")] if parsed_dict.get("summary") else [],
                education_summaries=[parsed_dict.get("education", "")] if parsed_dict.get("education") else [],
                key_strengths=candidate_skills[:4]
            )

        except Exception as e:
            logger.error(f"Failed to communicate with Groq parser API: {str(e)}", exc_info=True)
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=502,
                detail=f"External Groq AI service returned a parsing error: {str(e)}"
            )


    def chat_interview_question_stream(self, system_prompt: str, messages: List[Any]) -> Generator[str, None, None]:
        """
        Sends conversational memory logs to Groq API and streams the recruiter response back.
        Yields text token chunks dynamically with strict max_tokens boundaries.
        """
        if not self.client:
            logger.error("Groq client not initialized.")
            raise HTTPException(
                status_code=500,
                detail="Groq integration is not configured. Please supply a valid GROQ_API_KEY."
            )

        try:
            # Map running messages to Groq console specifications
            groq_messages: List[Any] = [{"role": "system", "content": system_prompt}]
            for msg in messages:
                role = msg.role if hasattr(msg, "role") else msg["role"]
                content = msg.content if hasattr(msg, "content") else msg["content"]
                groq_messages.append({"role": role, "content": content})

            # Stream chunks from Llama model
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                temperature=0.7,      # Natural conversational temperature
                max_tokens=150,       # Strict budget limit for recruiter question
                messages=groq_messages,  # type: ignore
                stream=True
            )

            for chunk in completion:
                if hasattr(chunk, "choices") and chunk.choices:
                    token = chunk.choices[0].delta.content
                    if token:
                        yield token

        except Exception as e:
            logger.error(f"Failed to stream response from Groq during chat turn: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=502,
                detail=f"External Groq conversational stream failed: {str(e)}"
            )

    def chat_interview_question_sync(self, system_prompt: str, messages: List[Any]) -> str:
        """
        Synchronous fallback for start endpoint or non-streaming unit tests.
        """
        if not self.client:
            raise HTTPException(
                status_code=500,
                detail="Groq integration is not configured. Please supply a valid GROQ_API_KEY."
            )

        try:
            groq_messages: List[Any] = [{"role": "system", "content": system_prompt}]
            for msg in messages:
                role = msg.role if hasattr(msg, "role") else msg["role"]
                content = msg.content if hasattr(msg, "content") else msg["content"]
                groq_messages.append({"role": role, "content": content})

            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=150,       # Strict budget limit for recruiter question
                messages=groq_messages  # type: ignore
            )
            content = response.choices[0].message.content
            return content.strip() if content else ""
        except Exception as e:
            logger.error(f"Failed to request Groq sync: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=502,
                detail=f"External Groq conversational API failed: {str(e)}"
            )

# Singleton service instance
llm_service = LLMService()
