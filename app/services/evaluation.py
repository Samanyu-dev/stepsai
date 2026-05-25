import logging
import json
from fpdf import FPDF
from threading import Lock
from typing import Dict, Optional, Tuple, List
from app.models.evaluation import FeedbackReport, AnswerEvaluation
from app.services.interview_engine import interview_engine
from app.services.llm import llm_service
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# --- Report stores ---
class InMemoryReportStore:
    """
    Thread-safe volatile memory store for compiling evaluations reports and PDF binaries.
    """
    def __init__(self):
        self._reports: Dict[str, FeedbackReport] = {}
        self._pdfs: Dict[str, bytes] = {}
        self._lock = Lock()

    def save_report(self, session_id: str, report: FeedbackReport, pdf_bytes: bytes):
        with self._lock:
            self._reports[session_id] = report
            self._pdfs[session_id] = pdf_bytes

    def get_report(self, session_id: str) -> Optional[FeedbackReport]:
        with self._lock:
            return self._reports.get(session_id)

    def get_pdf(self, session_id: str) -> Optional[bytes]:
        with self._lock:
            return self._pdfs.get(session_id)

report_store = InMemoryReportStore()


# --- Premium PDF generator ---
class PremiumFPDF(FPDF):
    """
    Custom FPDF2 class introducing consistent branding, header banners, 
    and bottom page numbering.
    """
    def header(self):
        if self.page_no() == 1:
            # Draw brand banner at the top of page 1
            self.set_fill_color(0, 85, 113)  # Brand dark teal #005571
            self.rect(0, 0, 210, 35, 'F')
            self.set_y(12)
            self.set_text_color(255, 255, 255)
            self.set_font('Helvetica', 'B', 16)
            self.cell(0, 10, 'STEPS AI MOCK INTERVIEW ASSESSMENT REPORT', 0, 1, 'C')
            self.set_y(40) # Push content position past header banner
        else:
            # Subtle header for subsequent pages
            self.set_text_color(100, 100, 100)
            self.set_font('Helvetica', 'B', 8)
            self.cell(0, 5, 'STEPS AI MOCK INTERVIEW - DETAILED PROFILE BREAKDOWN', 0, 1, 'L')
            self.set_draw_color(200, 200, 200)
            self.line(10, 15, 200, 15)
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Steps AI Hackathon 2026  |  Page {self.page_no()}', 0, 0, 'C')


class EvaluationService:
    """
    Orchestration layer evaluating conversational transcripts via Groq,
    aggregating scores, and compiling premium downloadable PDF reports.
    """
    def _extract_dialogue_pairs(self, messages: list) -> List[Tuple[str, str]]:
        """
        Parses chronological conversation memory list into sequential Q&A text pairs.
        """
        pairs = []
        last_question = None
        
        for msg in messages:
            role = msg.role if hasattr(msg, 'role') else msg.get('role', '')
            content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
            
            if role == "assistant":
                # Capture the recruiter's asked question
                last_question = content
            elif role == "user" and last_question:
                # Pair with the candidate's answer response
                pairs.append((last_question, content))
                last_question = None
                
        return pairs

    def evaluate_interview(self, session_id: str) -> FeedbackReport:
        """
        Fetches interview dialogue, formats prompt, triggers Groq JSON Mode scoring,
        and triggers PDF generation.
        """
        # 1. Fetch active session
        session = interview_engine.store.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="The specified interview session does not exist.")
            
        if not session.completed:
            # Force completion for grading
            session.completed = True
            interview_engine.store.save_session(session)

        # 2. Extract dialogue pairs
        pairs = self._extract_dialogue_pairs(session.messages)
        if not pairs:
            raise HTTPException(
                status_code=400, 
                detail="This interview session contains no conversational QA turns to evaluate."
            )

        # 3. Formulate transcript mapping
        transcript_str = ""
        for idx, (q, a) in enumerate(pairs, 1):
            transcript_str += f"TURN {idx}:\nRecruiter Question: {q}\nCandidate Answer: {a}\n\n"

        # 4. Prompt Groq for JSON-formatted multi-dimensional scoring rubrics
        system_prompt = (
            "You are an elite recruitment evaluator and career strategist. "
            "Analyze the mock interview transcript dialogs and evaluate each candidate answer response.\n"
            "You MUST return a JSON object matching this schema:\n"
            "{\n"
            "  \"overall_score\": 82,\n"
            "  \"strengths\": [\"List 3 top strengths observed...\"],\n"
            "  \"weaknesses\": [\"List 3 primary gap areas observed...\"],\n"
            "  \"summary_feedback\": \"Empathetic summary coaching paragraph...\",\n"
            "  \"evaluations\": [\n"
            "    {\n"
            "      \"question\": \"The actual question text...\",\n"
            "      \"answer\": \"The candidate's actual answer text...\",\n"
            "      \"clarity_score\": 8,\n"
            "      \"depth_score\": 7,\n"
            "      \"relevance_score\": 9,\n"
            "      \"confidence_score\": 8,\n"
            "      \"missing_concepts\": [\"caching\", \"MVCC\"],\n"
            "      \"improvement_tips\": [\"Direct tip 1\", \"Direct tip 2\"]\n"
            "    }\n"
            "  ]\n"
            "}\n\n"
            "GUIDELINES:\n"
            "- Grade scores clarity, depth, relevance, confidence on an integer scale out of 10.\n"
            "- Calculate overall_score out of 100 based on general performance.\n"
            "- Identify missing technical keywords/concepts per question.\n"
            "- Provide highly constructive coaching tips."
        )

        try:
            # Query Groq JSON mode
            response = llm_service.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
                temperature=0.0,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Please evaluate this transcript:\n\n{transcript_str}"}
                ]
            )

            raw_json = response.choices[0].message.content
            parsed_data = json.loads(raw_json)

            # Inject session details
            parsed_data["session_id"] = session_id
            parsed_data["estimated_job_role"] = session.estimated_job_role
            parsed_data["experience_level"] = session.difficulty_level.value

            # Build validated Pydantic report
            report = FeedbackReport(**parsed_data)

            # 5. Compile PDF report
            pdf_bytes = self.generate_pdf_report(report)

            # 6. Cache report and PDF bytes
            report_store.save_report(session_id, report, pdf_bytes)

            return report

        except Exception as e:
            logger.error(f"Failed to compile Groq evaluation report: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=502,
                detail=f"Generative AI grading gateway failed to analyze responses: {str(e)}"
            )

    def generate_pdf_report(self, report: FeedbackReport) -> bytes:
        """
        Uses FPDF2 to generate a premium branded PDF file stream.
        """
        try:
            pdf = PremiumFPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            
            # --- PAGE 1: OVERALL SCORECARD ---
            pdf.ln(25)  # Leave space for the banner
            
            # Candidate Meta Box
            pdf.set_fill_color(245, 247, 248)
            pdf.rect(10, 45, 190, 20, 'F')
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(50, 50, 50)
            pdf.text(15, 52, f"Target Role: {report.estimated_job_role}")
            pdf.text(15, 59, f"Seniority Level: {report.experience_level}")
            pdf.text(110, 52, f"Session ID: {report.session_id[:18]}...")
            pdf.text(110, 59, f"Status: Evaluation Completed")
            
            pdf.ln(18)
            
            # Big Score Box
            score = report.overall_score
            if score >= 80:
                color = (46, 125, 50)  # Green #2E7D32
            elif score >= 60:
                color = (239, 108, 0)  # Orange #EF6C00
            else:
                color = (198, 40, 40)  # Red #C62828
                
            pdf.set_fill_color(*color)
            pdf.rect(10, 70, 190, 25, 'F')
            pdf.set_font('Helvetica', 'B', 14)
            pdf.set_text_color(255, 255, 255)
            pdf.text(20, 85, f"OVERALL MOCK ASSESSMENT GRADE:")
            pdf.set_font('Helvetica', 'B', 22)
            pdf.text(150, 87, f"{score} / 100")
            
            pdf.ln(25)
            
            # Summary Feedback
            pdf.set_text_color(0, 85, 113)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.cell(0, 8, "EXECUTIVE SUMMARY FEEDBACK", 0, 1, 'L')
            pdf.set_draw_color(0, 85, 113)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)
            
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(70, 70, 70)
            pdf.multi_cell(0, 5, report.summary_feedback)
            pdf.ln(5)
            
            # Strengths & Weaknesses Split Grid
            pdf.set_font('Helvetica', 'B', 11)
            pdf.set_text_color(46, 125, 50)  # Strength Green
            pdf.cell(90, 6, "PROMINENT KEY STRENGTHS", 0, 0, 'L')
            pdf.set_text_color(198, 40, 40)  # Weakness Red
            pdf.cell(90, 6, "GROWTH & DEVELOPMENT AREAS", 0, 1, 'L')
            
            pdf.line(10, pdf.get_y(), 95, pdf.get_y())
            pdf.line(110, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)
            
            # Print strengths and weaknesses bullets side-by-side
            y_start = pdf.get_y()
            pdf.set_font('Helvetica', '', 9.5)
            pdf.set_text_color(60, 60, 60)
            
            # Write strengths
            pdf.set_xy(10, y_start)
            for strength in report.strengths[:4]:
                pdf.cell(5, 5, chr(127), 0, 0)  # Dot bullet
                pdf.multi_cell(80, 5, strength)
                pdf.set_x(10)
                
            y_strengths_end = pdf.get_y()
            
            # Write weaknesses
            pdf.set_xy(110, y_start)
            for weakness in report.weaknesses[:4]:
                pdf.cell(5, 5, chr(127), 0, 0)  # Dot bullet
                pdf.multi_cell(80, 5, weakness)
                pdf.set_x(110)
                
            y_weaknesses_end = pdf.get_y()
            
            # Reset cursor past the split grid
            pdf.set_y(max(y_strengths_end, y_weaknesses_end) + 8)
            
            # --- PAGE 2+: QUESTION BY QUESTION ---
            for idx, eval_item in enumerate(report.evaluations, 1):
                pdf.add_page()
                pdf.ln(8)
                
                # Question header
                pdf.set_text_color(0, 85, 113)
                pdf.set_font('Helvetica', 'B', 12)
                pdf.cell(0, 6, f"QUESTION {idx} EVALUATION BREAKDOWN", 0, 1, 'L')
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(4)
                
                # Print Question text in light box
                pdf.set_fill_color(240, 244, 245)
                pdf.set_font('Helvetica', 'B', 9.5)
                pdf.set_text_color(40, 40, 40)
                pdf.multi_cell(0, 5, f"Q: {eval_item.question}", fill=True)
                pdf.ln(2)
                
                # Print Candidate Answer text
                pdf.set_font('Helvetica', 'I', 9)
                pdf.set_text_color(80, 80, 80)
                pdf.multi_cell(0, 5, f"Candidate Response:\n\"{eval_item.answer}\"")
                pdf.ln(5)
                
                # Sub Scoring Box (Clarity, Depth, Relevance, Confidence)
                pdf.set_fill_color(245, 247, 248)
                pdf.rect(10, pdf.get_y(), 190, 15, 'F')
                pdf.set_font('Helvetica', 'B', 8.5)
                pdf.set_text_color(50, 50, 50)
                
                y_box = pdf.get_y() + 4
                pdf.text(15, y_box, f"Clarity: {eval_item.clarity_score}/10")
                pdf.text(60, y_box, f"Tech Depth: {eval_item.depth_score}/10")
                pdf.text(110, y_box, f"Relevance: {eval_item.relevance_score}/10")
                pdf.text(155, y_box, f"Confidence: {eval_item.confidence_score}/10")
                
                pdf.ln(18)
                
                # Gaps & tips bullets
                pdf.set_font('Helvetica', 'B', 9.5)
                pdf.set_text_color(198, 40, 40)
                pdf.cell(0, 5, "TECHNICAL CONCEPTS GAPS / OMITTED KEYWORDS:", 0, 1, 'L')
                pdf.set_font('Helvetica', '', 9)
                pdf.set_text_color(60, 60, 60)
                if eval_item.missing_concepts:
                    pdf.multi_cell(0, 5, ", ".join(eval_item.missing_concepts))
                else:
                    pdf.cell(0, 5, "None detected. The technical keywords usage was solid.", 0, 1, 'L')
                pdf.ln(4)
                
                pdf.set_font('Helvetica', 'B', 9.5)
                pdf.set_text_color(46, 125, 50)
                pdf.cell(0, 5, "CONSTRUCTIVE COACHING TIPS FOR IMPROVEMENT:", 0, 1, 'L')
                pdf.set_font('Helvetica', '', 9)
                pdf.set_text_color(60, 60, 60)
                for tip in eval_item.improvement_tips:
                    pdf.cell(5, 5, "-", 0, 0)
                    pdf.multi_cell(0, 5, tip)
                    pdf.set_x(10)
            
            # Output PDF to bytes
            return bytes(pdf.output(dest='S'))
            
        except Exception as e:
            logger.error(f"Failed to generate PDF document structure: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while compiling the PDF layout: {str(e)}"
            )

# Singleton service
evaluation_service = EvaluationService()
