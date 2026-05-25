import logging
import json
from groq import Groq
from app.core.config import settings
from app.models.resume import ResumeProfile
from fastapi import HTTPException
from typing import Generator

logger = logging.getLogger(__name__)

class LLMService:
    """
    Service gateway mapping generative AI pipelines (specifically Groq's llama-3.3-70b-versatile)
    to parse resume contents and stream conversational responses.
    """
    def __init__(self):
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
        to extract structured candidate details matching the ResumeProfile schema.
        """
        if not self.client:
            logger.error("Groq client not initialized. GROQ_API_KEY environment variable is missing.")
            raise HTTPException(
                status_code=500,
                detail="Groq integration is not configured. Please supply a valid GROQ_API_KEY."
            )

        # Describe the Pydantic structure for the model prompt
        schema_instructions = (
            "Return a JSON object with the following fields and types:\n"
            "- candidate_name (string or null): Candidate full name\n"
            "- email (string or null): E-mail address\n"
            "- phone (string or null): Contact phone number\n"
            "- linkedin (string or null): LinkedIn URL\n"
            "- github (string or null): GitHub URL\n"
            "- estimated_job_role (string): Target engineering role (e.g. Backend Developer, Data Scientist)\n"
            "- experience_level (string): Seniority level (Intern, Junior, Mid-level, Senior, Lead)\n"
            "- skills (array of strings): Core programming skills, libraries, frameworks\n"
            "- work_experience_summaries (array of strings): Brief summaries of past jobs and roles\n"
            "- education_summaries (array of strings): Brief academic/education summaries\n"
            "- key_strengths (array of strings): Standout strengths or accomplishments\n"
        )

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
                temperature=0.0,  # Strict deterministic extraction
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an elite resume parser. Analyze the resume text and extract structured profile details. "
                            f"You MUST return a JSON object strictly matching the following schema:\n{schema_instructions}"
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Parse the following resume text:\n\n{resume_text}"
                    }
                ]
            )

            raw_json = response.choices[0].message.content
            parsed_dict = json.loads(raw_json)
            
            # Map dictionary fields to validated ResumeProfile Pydantic representation
            return ResumeProfile(**parsed_dict)

        except Exception as e:
            logger.error(f"Failed to communicate with Groq parser API: {str(e)}", exc_info=True)
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=502,
                detail=f"External Groq AI service returned a parsing error: {str(e)}"
            )

    def chat_interview_question_stream(self, system_prompt: str, messages: list) -> Generator[str, None, None]:
        """
        Sends conversational memory logs to Groq API and streams the recruiter response back.
        Yields text token chunks dynamically.
        """
        if not self.client:
            logger.error("Groq client not initialized.")
            raise HTTPException(
                status_code=500,
                detail="Groq integration is not configured. Please supply a valid GROQ_API_KEY."
            )

        try:
            # Map running messages to Groq console specifications
            groq_messages = [{"role": "system", "content": system_prompt}]
            for msg in messages:
                role = msg.role if hasattr(msg, "role") else msg["role"]
                content = msg.content if hasattr(msg, "content") else msg["content"]
                groq_messages.append({"role": role, "content": content})

            # Stream chunks from Llama model
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                temperature=0.7,  # Natural conversational temperature
                messages=groq_messages,
                stream=True
            )

            for chunk in completion:
                token = chunk.choices[0].delta.content
                if token:
                    yield token

        except Exception as e:
            logger.error(f"Failed to stream response from Groq during chat turn: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=502,
                detail=f"External Groq conversational stream failed: {str(e)}"
            )

    def chat_interview_question_sync(self, system_prompt: str, messages: list) -> str:
        """
        Synchronous fallback for start endpoint or non-streaming unit tests.
        """
        if not self.client:
            raise HTTPException(
                status_code=500,
                detail="Groq integration is not configured. Please supply a valid GROQ_API_KEY."
            )

        try:
            groq_messages = [{"role": "system", "content": system_prompt}]
            for msg in messages:
                role = msg.role if hasattr(msg, "role") else msg["role"]
                content = msg.content if hasattr(msg, "content") else msg["content"]
                groq_messages.append({"role": role, "content": content})

            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                messages=groq_messages
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Failed to request Groq sync: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=502,
                detail=f"External Groq conversational API failed: {str(e)}"
            )

# Singleton service instance
llm_service = LLMService()
