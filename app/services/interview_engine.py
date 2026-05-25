"""
Steps AI Mock Interview Conversational Engine.

This module manages the full interview session state, Recruiter Alex prompts,
dynamic progression, vague answer checks, question deduplication, and database operations.
"""

import uuid
import logging
import json
from typing import Dict, List, Optional, Generator, Any
from app.models.interview import Message, InterviewMode, DifficultyLevel
from app.models.resume import ResumeProfile
from app.services.llm import llm_service
from app.core.db import get_db_connection
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# --- SQLite-Backed Resume store ---
class InMemoryResumeStore:
    """
    Persistent SQLite-backed store for parsed candidate profiles (Phase 2).
    """
    def save_profile(self, profile: ResumeProfile) -> str:
        session_id = str(uuid.uuid4())
        profile_json = profile.model_dump_json()
        resume_text = profile.summary or ""
        
        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO resumes (session_id, profile_json, resume_text) VALUES (?, ?, ?)",
                (session_id, profile_json, resume_text)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to save resume in SQLite: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Database write error on resume profiling.")
        finally:
            conn.close()
        return session_id

    def get_profile(self, session_id: str) -> Optional[ResumeProfile]:
        conn = get_db_connection()
        try:
            row = conn.execute("SELECT profile_json FROM resumes WHERE session_id = ?", (session_id,)).fetchone()
            if row:
                profile_dict = json.loads(row["profile_json"])
                return ResumeProfile(**profile_dict)
        except Exception as e:
            logger.error(f"Failed to fetch resume from SQLite: {str(e)}", exc_info=True)
        finally:
            conn.close()
        return None

resume_store = InMemoryResumeStore()


# --- Interview session state container ---
class InterviewSession:
    """
    State container representing an active mock interview session.
    """
    def __init__(
        self,
        interview_session_id: str,
        resume_session_id: str,
        interview_mode: InterviewMode,
        difficulty_level: DifficultyLevel,
        total_questions: int,
        resume_context: Dict[str, Any]
    ) -> None:
        self.interview_session_id = interview_session_id
        self.resume_session_id = resume_session_id
        self.interview_mode = interview_mode
        self.difficulty_level = difficulty_level
        self.current_question_index = 1
        self.total_questions = total_questions
        self.messages: List[Message] = []
        self.asked_questions: List[str] = []
        self.completed = False
        self.resume_context = resume_context
        self.estimated_job_role = resume_context.get("estimated_job_role", "Software Engineer")


# --- SQLite-Backed Interview session store ---
class InMemoryInterviewStore:
    """
    Persistent SQLite-backed store for active mock interviews (Phase 3).
    """
    def create_session(
        self,
        resume_session_id: str,
        interview_mode: InterviewMode,
        difficulty_level: DifficultyLevel,
        total_questions: int,
        resume_profile: ResumeProfile
    ) -> InterviewSession:
        interview_session_id = str(uuid.uuid4())
        resume_context = resume_profile.model_dump()
        messages_payload: Dict[str, Any] = {
            "messages": [],
            "asked_questions": []
        }
        
        conn = get_db_connection()
        try:
            conn.execute(
                """
                INSERT INTO interviews 
                (interview_session_id, resume_session_id, interview_mode, difficulty_level, 
                 current_question_index, total_questions, messages_json, completed, resume_context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    interview_session_id,
                    resume_session_id,
                    interview_mode.value,
                    difficulty_level.value,
                    1,
                    total_questions,
                    json.dumps(messages_payload),
                    0,
                    json.dumps(resume_context)
                )
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to create interview session in SQLite: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Database write error on session creation.")
        finally:
            conn.close()
            
        return InterviewSession(
            interview_session_id=interview_session_id,
            resume_session_id=resume_session_id,
            interview_mode=interview_mode,
            difficulty_level=difficulty_level,
            total_questions=total_questions,
            resume_context=resume_context
        )

    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        conn = get_db_connection()
        try:
            row = conn.execute("SELECT * FROM interviews WHERE interview_session_id = ?", (session_id,)).fetchone()
            if row:
                session = InterviewSession(
                    interview_session_id=row["interview_session_id"],
                    resume_session_id=row["resume_session_id"],
                    interview_mode=InterviewMode(row["interview_mode"]),
                    difficulty_level=DifficultyLevel(row["difficulty_level"]),
                    total_questions=row["total_questions"],
                    resume_context=json.loads(row["resume_context"])
                )
                session.current_question_index = row["current_question_index"]
                session.completed = bool(row["completed"])
                
                # Deserialize messages history list and asked questions list
                raw_payload = json.loads(row["messages_json"])
                if isinstance(raw_payload, dict) and "messages" in raw_payload:
                    msgs_list = raw_payload["messages"]
                    session.asked_questions = raw_payload.get("asked_questions", [])
                else:
                    msgs_list = raw_payload
                    session.asked_questions = []
                    
                session.messages = [Message(**m) for m in msgs_list]
                return session
        except Exception as e:
            logger.error(f"Failed to fetch session from SQLite: {str(e)}", exc_info=True)
        finally:
            conn.close()
        return None

    def save_session(self, session: InterviewSession) -> None:
        conn = get_db_connection()
        try:
            msgs_list = [m.model_dump() for m in session.messages]
            messages_payload: Dict[str, Any] = {
                "messages": msgs_list,
                "asked_questions": session.asked_questions
            }
            conn.execute(
                """
                UPDATE interviews 
                SET current_question_index = ?, difficulty_level = ?, messages_json = ?, completed = ?
                WHERE interview_session_id = ?
                """,
                (
                    session.current_question_index,
                    session.difficulty_level.value,
                    json.dumps(messages_payload),
                    1 if session.completed else 0,
                    session.interview_session_id
                )
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to update session in SQLite: {str(e)}", exc_info=True)
        finally:
            conn.close()


# --- Orchestrating Interview Engine ---
class InterviewEngine:
    """
    Orchestration engine driving syllabus generation, recruiter personas,
    adaptive difficulty tiers progressions, and SSE streaming.
    """
    def __init__(self) -> None:
        self.store = InMemoryInterviewStore()

    def _adapt_difficulty_tier(self, session: InterviewSession, last_answer: str) -> None:
        """
        Dynamically analyzes the candidate's last answer and adjusts the session difficulty level
        (Junior -> Mid -> Senior, corresponding to Easy -> Medium -> Hard prompts).
        """
        answer_len = len(last_answer)
        if answer_len < 40:
            # Decrease difficulty if possible due to weak/brief answer quality
            if session.difficulty_level == DifficultyLevel.SENIOR:
                session.difficulty_level = DifficultyLevel.MID
            elif session.difficulty_level == DifficultyLevel.MID:
                session.difficulty_level = DifficultyLevel.JUNIOR
            logger.info(f"Session {session.interview_session_id}: decreased difficulty to {session.difficulty_level.value} due to brief answer ({answer_len} chars).")
        elif answer_len > 120:
            # Increase difficulty if possible due to detailed/strong answer quality
            if session.difficulty_level == DifficultyLevel.JUNIOR:
                session.difficulty_level = DifficultyLevel.MID
            elif session.difficulty_level == DifficultyLevel.MID:
                session.difficulty_level = DifficultyLevel.SENIOR
            logger.info(f"Session {session.interview_session_id}: increased difficulty to {session.difficulty_level.value} due to detailed answer ({answer_len} chars).")

    def _assess_answer_quality(self, answer: str) -> str:
        """Returns 'weak' or 'adequate' based on answer content heuristics."""
        stripped = answer.strip()
        if len(stripped) < 80:
            return "weak"
        weak_phrases = ["i think", "maybe", "not sure", "i don't know", 
                        "i am not sure", "i guess", "probably", "i'm not sure"]
        if any(phrase in stripped.lower() for phrase in weak_phrases):
            return "weak"
        return "adequate"

    def _build_adaptive_recruiter_prompt(self, session: InterviewSession) -> str:
        """
        Assembles strict technical recruiter prompt injecting current candidate context,
        turn transcript, last answer assessment, and dynamic difficulty parameters.
        """
        context = session.resume_context
        skills_str = ", ".join(context.get("skills", ["Python", "System Design"]))
        experience_years = context.get("experience_years", 2)
        seniority = session.difficulty_level.value
        job_role = session.estimated_job_role
        mode = session.interview_mode.value
        
        # Determine difficulty label
        difficulty_label = "Medium"
        if seniority == "Junior":
            difficulty_label = "Easy"
        elif seniority == "Senior":
            difficulty_label = "Hard"

        # Build conversation transcript
        transcript_turns = []
        pairs = []
        last_question = "N/A"
        last_answer = "N/A"
        
        for msg in session.messages:
            if msg.role == "assistant":
                last_question = msg.content
            elif msg.role == "user" and last_question != "N/A":
                pairs.append((last_question, msg.content))
                last_question = "N/A"
                
        for idx, (q, a) in enumerate(pairs, 1):
            transcript_turns.append(f"Turn {idx}:\nQuestion: {q}\nAnswer: {a}\n")
            
        transcript = "\n".join(transcript_turns) if transcript_turns else "None (Mock interview has just started)"
        
        if pairs:
            last_question = pairs[-1][0]
            last_answer = pairs[-1][1]

        prompt = (
            "You are a strict, senior technical interviewer at a top-tier company.\n\n"
            "Candidate profile:\n"
            f"- Role: {job_role}\n"
            f"- Seniority: {seniority}\n"
            f"- Skills: {skills_str}\n"
            f"- Experience: {experience_years} years\n\n"
            f"Interview mode: {mode}  # HR | Technical | Behavioral\n"
            f"Difficulty: {difficulty_label}  # Easy | Medium | Hard\n\n"
            "Rules:\n"
            "- Ask ONE question at a time, never two\n"
            "- Each question must be different from previous ones\n"
            "- Adapt difficulty based on answer quality\n"
            "- If answer is vague or wrong, ask a follow-up probing the same concept\n"
            "- If answer is strong, move to a harder concept\n"
            "- Never reveal scoring or evaluation\n"
            "- Never say \"Great answer!\" or give positive feedback mid-interview\n"
            "- Keep questions under 3 sentences\n"
            f"- For Technical: focus on {skills_str}\n"
            "- For HR: focus on motivation, culture fit, conflict resolution\n"
            "- For Behavioral: use STAR-method prompting situations\n\n"
            f"Start with: ask a warm-up question appropriate for {seniority} {job_role}.\n\n"
            f"You are conducting a {mode} interview for a {seniority} {job_role}.\n\n"
            "Conversation so far:\n"
            f"{transcript}\n\n"
            f"Last question asked: {last_question}\n"
            f"Candidate's answer: {last_answer}\n\n"
            "Internally assess (do NOT output this):\n"
            "- Was the answer correct/complete? (yes/partial/no)\n"
            "- Was it vague or specific?\n"
            "- What concept did it test?\n\n"
            "Then output ONLY the next interview question. One question. No preamble. No feedback. No \"I see\" or \"Good point\".\n"
            "If answer was weak, probe deeper on the same concept.\n"
            "If answer was strong, advance to a harder related concept.\n"
            f"If this is question {session.current_question_index} of {session.total_questions}, make it appropriately conclusive."
        )
        if len(session.asked_questions) > 0:
            questions_list = "\n".join(session.asked_questions[-5:])
            prompt += f"\n\nDo NOT repeat any of these previously asked questions:\n{questions_list}"
        return prompt

    def start_interview(
        self,
        resume_session_id: str,
        interview_mode: InterviewMode,
        difficulty_level: Optional[DifficultyLevel],
        total_questions: int = 5
    ) -> InterviewSession:
        """
        Launches session, calculates difficulty, and synchronous fetches opening question Q1.
        """
        # Fetch profile from store
        profile = resume_store.get_profile(resume_session_id)
        if not profile:
            raise HTTPException(
                status_code=404, 
                detail="Resume session profile not found. Please upload a resume first."
            )

        # Auto-detect seniority level if None is supplied
        if not difficulty_level:
            level_str_sen = (profile.seniority or "Junior").lower()
            level_str_exp = (profile.experience_level or "Junior").lower()
            
            if ("senior" in level_str_sen or "lead" in level_str_sen or "principal" in level_str_sen or
                "senior" in level_str_exp or "lead" in level_str_exp or "principal" in level_str_exp):
                difficulty_level = DifficultyLevel.SENIOR
            elif "mid" in level_str_sen or "experience" in level_str_sen or "mid" in level_str_exp or "experience" in level_str_exp:
                difficulty_level = DifficultyLevel.MID
            else:
                difficulty_level = DifficultyLevel.JUNIOR

        session = self.store.create_session(
            resume_session_id=resume_session_id,
            interview_mode=interview_mode,
            difficulty_level=difficulty_level,
            total_questions=total_questions,
            resume_profile=profile
        )

        system_prompt = self._build_adaptive_recruiter_prompt(session)
        opening_prompt = [
            Message(
                role="user", 
                content=f"Please introduce yourself warmly, state the parameters, and ask the warm-up question based on the resume target role {session.estimated_job_role}."
            )
        ]

        first_question = llm_service.chat_interview_question_sync(system_prompt, opening_prompt)
        session.messages.append(Message(role="assistant", content=first_question))
        session.asked_questions.append(first_question)
        self.store.save_session(session)
        return session

    def progress_interview_stream(
        self,
        session_id: str,
        candidate_answer: str
    ) -> Generator[str, None, None]:
        """
        Appends response, determines turn index, and yields streaming token chunks via SSE.
        Saves full assistant response upon generator completion.
        """
        session = self.store.get_session(session_id)
        if not session:
            logger.error(f"Failed session fetch: {session_id}")
            raise HTTPException(status_code=404, detail="The specified interview session does not exist.")
            
        if session.completed:
            logger.warning(f"Attempted progress on closed session: {session_id}")
            raise HTTPException(status_code=400, detail="This mock interview session is already completed.")

        # 1. Store candidate answer
        session.messages.append(Message(role="user", content=candidate_answer))

        # 2. Adapt difficulty dynamically based on answer quality
        self._adapt_difficulty_tier(session, candidate_answer)

        # 3. Check if final allocated turn
        if session.current_question_index >= session.total_questions:
            concluding_prompt = self._build_adaptive_recruiter_prompt(session) + (
                "\n\n--- ACTION REQUIRED ---\n"
                "The candidate has responded to your final question. "
                "Briefly acknowledge their answer, thank them warmly for their time, "
                "and clearly state that the mock interview is now completed. Do not ask any more questions."
            )
            
            # Setup concluding stream
            full_response_list = []
            try:
                for chunk in llm_service.chat_interview_question_stream(concluding_prompt, session.messages):
                    full_response_list.append(chunk)
                    yield chunk
            finally:
                response_text = "".join(full_response_list).strip()
                if response_text:
                    session.messages.append(Message(role="assistant", content=response_text))
                    session.asked_questions.append(response_text)
                session.completed = True
                self.store.save_session(session)
            return

        # 4. Otherwise, progress and stream next question
        session.current_question_index += 1
        
        # Assess quality and log
        quality = self._assess_answer_quality(candidate_answer)
        logger.debug(f"Answer quality for session {session_id}: {quality}")
        
        system_prompt = self._build_adaptive_recruiter_prompt(session)
        if quality == "weak":
            system_prompt = (
                "IMPORTANT: The candidate just gave a vague or incomplete answer. Ask a targeted "
                "follow-up probing the SAME concept. Do not advance to a new topic.\n\n"
            ) + system_prompt
        
        full_response_list = []
        try:
            for chunk in llm_service.chat_interview_question_stream(system_prompt, session.messages):
                full_response_list.append(chunk)
                yield chunk
        finally:
            response_text = "".join(full_response_list).strip()
            if response_text:
                session.messages.append(Message(role="assistant", content=response_text))
                session.asked_questions.append(response_text)
            self.store.save_session(session)

# Singleton orchestrator
interview_engine = InterviewEngine()
