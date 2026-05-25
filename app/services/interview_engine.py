import uuid
import logging
from threading import Lock
from typing import Dict, List, Optional, Generator
from app.models.interview import Message, InterviewMode, DifficultyLevel
from app.models.resume import ResumeProfile
from app.services.llm import llm_service
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# --- Resume session store ---
class InMemoryResumeStore:
    """
    Thread-safe volatile memory store for parsed candidate profiles (Phase 2).
    """
    def __init__(self):
        self._profiles: Dict[str, ResumeProfile] = {}
        self._lock = Lock()

    def save_profile(self, profile: ResumeProfile) -> str:
        session_id = str(uuid.uuid4())
        with self._lock:
            self._profiles[session_id] = profile
        return session_id

    def get_profile(self, session_id: str) -> Optional[ResumeProfile]:
        with self._lock:
            return self._profiles.get(session_id)

resume_store = InMemoryResumeStore()


# --- Interview session store ---
class InterviewSession:
    """
    Volatile state container representing an active mock interview session.
    """
    def __init__(
        self,
        interview_session_id: str,
        resume_session_id: str,
        interview_mode: InterviewMode,
        difficulty_level: DifficultyLevel,
        total_questions: int,
        resume_context: dict
    ):
        self.interview_session_id = interview_session_id
        self.resume_session_id = resume_session_id
        self.interview_mode = interview_mode
        self.difficulty_level = difficulty_level
        self.current_question_index = 1
        self.total_questions = total_questions
        self.messages: List[Message] = []
        self.completed = False
        self.resume_context = resume_context
        self.estimated_job_role = resume_context.get("estimated_job_role", "Software Engineer")

class InMemoryInterviewStore:
    """
    Thread-safe store for active mock interviews (Phase 3).
    """
    def __init__(self):
        self._sessions: Dict[str, InterviewSession] = {}
        self._lock = Lock()

    def create_session(
        self,
        resume_session_id: str,
        interview_mode: InterviewMode,
        difficulty_level: DifficultyLevel,
        total_questions: int,
        resume_profile: ResumeProfile
    ) -> InterviewSession:
        interview_session_id = str(uuid.uuid4())
        session = InterviewSession(
            interview_session_id=interview_session_id,
            resume_session_id=resume_session_id,
            interview_mode=interview_mode,
            difficulty_level=difficulty_level,
            total_questions=total_questions,
            resume_context=resume_profile.model_dump()
        )
        with self._lock:
            self._sessions[interview_session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        with self._lock:
            return self._sessions.get(session_id)

    def save_session(self, session: InterviewSession):
        with self._lock:
            self._sessions[session.interview_session_id] = session

class InterviewEngine:
    """
    Orchestration engine driving syllabus generation, recruiter personas,
    and Server-Sent Events (SSE) streaming progress.
    """
    def __init__(self):
        self.store = InMemoryInterviewStore()

    def _build_system_prompt(self, session: InterviewSession) -> str:
        """
        Assembles comprehensive recruiter system prompt injecting candidates context,
        the active mode parameters (HR, Technical, Behavioral), and current index.
        """
        context = session.resume_context
        skills_str = ", ".join(context.get("skills", []))
        candidate_name = context.get("candidate_name") or "Candidate"
        
        # Customize structural question focus based on mode selection
        if session.interview_mode == InterviewMode.HR:
            syllabus_details = (
                "1. Question 1 (Background & Warm Welcome): Introductory greetings and background walkthrough.\n"
                "2. Question 2 (Teamwork & Collaboration): Experience handling group tasks, remote syncs, or disagreements.\n"
                "3. Question 3 (Prioritization & Pressure): Resolving strict deadlines or scope shifts.\n"
                "4. Question 4 (Conflict Resolution): Under pressure case study or dealing with a difficult peer.\n"
                "5. Question 5 (HR / Values / Salary Expectations): Cultural values, salary brackets, and closing.\n"
            )
            mode_instruction = "HR Recruiter focusing on communication, values, remote synchronization, and organizational skills."
        elif session.interview_mode == InterviewMode.BEHAVIORAL:
            syllabus_details = (
                "1. Question 1 (Background & Warm Welcome): Introduction and walkthrough of recent experiences.\n"
                "2. Question 2 (STAR Scenario - Technical Failure): Detail a significant technical challenge or project failure and outcome.\n"
                "3. Question 3 (STAR Scenario - Conflict): Handling strict deadlines, technical disagreements, or client problems.\n"
                "4. Question 4 (STAR Scenario - Leadership): A time when the candidate took initiative or led a task.\n"
                "5. Question 5 (HR / Career Drivers): Closing discussion on goals and mock closure.\n"
            )
            mode_instruction = "Behavioral Coach probing concrete experiences using the STAR method (Situation, Task, Action, Result)."
        else: # Technical Mode
            syllabus_details = (
                "1. Question 1 (Background & Warm Welcome): Welcome and short architectural walkthrough of their major project.\n"
                "2. Question 2 (Core Technical Concept): In-depth query targeting language features or framework mechanics (e.g. async/threads, memory).\n"
                "3. Question 3 (System Architecture Design): Scalability, database selections, queue processing, or microservice components.\n"
                "4. Question 4 (Under Pressure Scenario): Handling production system outages or bugs under strict deadlines.\n"
                "5. Question 5 (HR / Career Alignment): Long-term technical trajectory and mock closing.\n"
            )
            mode_instruction = "Senior Technical Interviewer checking coding mechanics, systems architecture decisions, and scaling issues."

        prompt = (
            "You are Alex, an elite, highly empathetic AI Recruiter at Steps AI. "
            "Your objective is to conduct a highly professional, conversational mock interview.\n\n"
            f"--- MOCK INTERVIEW PARAMETERS ---\n"
            f"- Recruiter Persona Focus: {mode_instruction}\n"
            f"- Target Interview Mode: {session.interview_mode.value}\n"
            f"- Seniority Level: {session.difficulty_level.value}\n\n"
            f"--- CANDIDATE PROFILE INFO ---\n"
            f"- Candidate Name: {candidate_name}\n"
            f"- Estimated Job Role: {session.estimated_job_role}\n"
            f"- Core Skills: {skills_str}\n"
            f"- Experience Summaries: {', '.join(context.get('work_experience_summaries', []))}\n"
            f"- Education: {', '.join(context.get('education_summaries', []))}\n\n"
            f"--- INTERVIEW SYLLABUS ---\n{syllabus_details}\n"
            f"--- MANDATORY GUIDELINES ---\n"
            "- Speak naturally, conversationally, and with professional empathy. Do NOT sound like a robotic checklist.\n"
            f"- The interview has a strict limit of exactly {session.total_questions} questions.\n"
            f"- You are CURRENTLY presenting Question {session.current_question_index} out of {session.total_questions}.\n"
            "- **IMPORTANT**: Ask exactly ONE question at a time. Do not compile multiple queries or checklists.\n"
            "- Acknowledge the candidate's preceding response with highly professional, brief transition feedback before pivoting.\n"
            "- Customize question complexities to fit their seniority tier."
        )
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
            level_str = profile.experience_level.lower()
            if "senior" in level_str or "lead" in level_str or "principal" in level_str:
                difficulty_level = DifficultyLevel.SENIOR
            elif "mid" in level_str or "experience" in level_str:
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

        system_prompt = self._build_system_prompt(session)
        opening_prompt = [
            Message(
                role="user", 
                content="Please introduce yourself warmly, state the interview parameters, and ask the first syllabus question based on the resume."
            )
        ]

        first_question = llm_service.chat_interview_question_sync(system_prompt, opening_prompt)
        session.messages.append(Message(role="assistant", content=first_question))
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

        # 2. Check if final allocated turn
        if session.current_question_index >= session.total_questions:
            concluding_prompt = self._build_system_prompt(session) + (
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
                session.completed = True
                self.store.save_session(session)
            return

        # 3. Otherwise, progress and stream next question
        session.current_question_index += 1
        system_prompt = self._build_system_prompt(session)
        
        full_response_list = []
        try:
            for chunk in llm_service.chat_interview_question_stream(system_prompt, session.messages):
                full_response_list.append(chunk)
                yield chunk
        finally:
            response_text = "".join(full_response_list).strip()
            if response_text:
                session.messages.append(Message(role="assistant", content=response_text))
            self.store.save_session(session)

# Singleton orchestrator
interview_engine = InterviewEngine()
