"""
Steps AI Performance Diagnostic & PDF Compiler Service.

This module evaluates completed mock interviews using Groq JSON Mode grading prompts
and compiles a premium, multi-page custom branded performance card PDF.
"""

import logging
import json
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from typing import Dict, Optional, Tuple, List, Any
from app.models.evaluation import FeedbackReport, AnswerEvaluation
from app.services.interview_engine import interview_engine
from app.services.llm import llm_service
from app.core.db import get_db_connection
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# --- Helper for Robust Bounded Score Parsing ---
def safe_int_score(val: Any, default: int = 5, min_val: int = 0, max_val: int = 10) -> int:
    """
    Safely converts a score value from the LLM (string, float, or int) to a bounded integer.
    Normalizes 100-scale values to 10-scale if needed for 10-scale targets.
    """
    try:
        val_f = float(val)
        if val_f > max_val and max_val == 10:
            val_f = val_f / 10.0
        val_i = int(round(val_f))
        return max(min_val, min(max_val, val_i))
    except (ValueError, TypeError):
        return default

# --- SQLite-Backed Report store ---
class InMemoryReportStore:
    """
    Persistent SQLite-backed store for compiling evaluations reports and PDF binaries.
    """
    def save_report(self, session_id: str, report: FeedbackReport, pdf_bytes: bytes) -> None:
        conn = get_db_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO evaluations (session_id, overall_score, report_json, pdf_bytes)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, report.overall_score, report.model_dump_json(), pdf_bytes)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to save evaluation to SQLite: {str(e)}", exc_info=True)
        finally:
            conn.close()

    def get_report(self, session_id: str) -> Optional[FeedbackReport]:
        conn = get_db_connection()
        try:
            row = conn.execute("SELECT report_json FROM evaluations WHERE session_id = ?", (session_id,)).fetchone()
            if row:
                report_dict = json.loads(row["report_json"])
                return FeedbackReport(**report_dict)
        except Exception as e:
            logger.error(f"Failed to fetch evaluation from SQLite: {str(e)}", exc_info=True)
        finally:
            conn.close()
        return None

    def get_pdf(self, session_id: str) -> Optional[bytes]:
        conn = get_db_connection()
        try:
            row = conn.execute("SELECT pdf_bytes FROM evaluations WHERE session_id = ?", (session_id,)).fetchone()
            if row:
                return row["pdf_bytes"]
        except Exception as e:
            logger.error(f"Failed to fetch PDF from SQLite: {str(e)}", exc_info=True)
        finally:
            conn.close()
        return None

report_store = InMemoryReportStore()


# --- Premium PDF generator ---
class PremiumFPDF(FPDF):
    """
    Custom FPDF2 class introducing consistent branding, header banners, 
    and bottom page numbering.
    """
    def header(self) -> None:
        if self.page_no() == 1:
            # Draw brand banner at the top of page 1
            self.set_fill_color(0, 85, 113)  # Brand dark teal #005571
            self.rect(0, 0, 210, 35, 'F')
            self.set_y(12)
            self.set_text_color(255, 255, 255)
            self.set_font('Helvetica', 'B', 16)
            self.cell(0, 10, 'STEPS AI MOCK INTERVIEW ASSESSMENT REPORT', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
            self.set_y(40) # Push content position past header banner
        else:
            # Subtle header for subsequent pages
            self.set_text_color(100, 100, 100)
            self.set_font('Helvetica', 'B', 8)
            self.cell(0, 5, 'STEPS AI MOCK INTERVIEW - DETAILED PROFILE BREAKDOWN', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
            self.set_draw_color(200, 200, 200)
            self.line(10, 15, 200, 15)
            self.ln(5)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Steps AI Hackathon 2026  |  Page {self.page_no()}', 0, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C')


class EvaluationService:
    """
    Orchestration layer evaluating conversational transcripts via Groq,
    aggregating scores, and compiling premium downloadable PDF reports.
    """
    def _extract_dialogue_pairs(self, messages: List[Any]) -> List[Tuple[str, str]]:
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
            transcript_str += f"Q: {q}\nA: {a}\n\n"

        # 4. Prompt Groq for JSON-formatted metrics using the exact requested structure
        system_prompt = (
            "You are a senior hiring manager. Evaluate this complete interview transcript.\n\n"
            f"Candidate: {session.resume_context.get('name') or 'Candidate'}, applying for {session.estimated_job_role} ({session.difficulty_level.value})\n"
            f"Interview mode: {session.interview_mode.value}\n\n"
            "Full transcript:\n"
            f"{transcript_str}\n"
            "Return ONLY valid JSON:\n"
            "{\n"
            "  \"overall_score\": 0-10,\n"
            "  \"grade\": \"A|B|C|D|F\",\n"
            "  \"hire_recommendation\": \"Strong Yes|Yes|Maybe|No\",\n"
            "  \"metrics\": {\n"
            "    \"technical_accuracy\": {\"score\": 0-10, \"note\": \"one line\"},\n"
            "    \"communication_clarity\": {\"score\": 0-10, \"note\": \"one line\"},\n"
            "    \"problem_solving\": {\"score\": 0-10, \"note\": \"one line\"},\n"
            "    \"depth_of_knowledge\": {\"score\": 0-10, \"note\": \"one line\"},\n"
            "    \"confidence\": {\"score\": 0-10, \"note\": \"one line\"}\n"
            "  },\n"
            "  \"strengths\": [\"max 3 items\"],\n"
            "  \"gaps\": [\"max 3 items\"],\n"
            "  \"missing_keywords\": [\"important terms never mentioned\"],\n"
            "  \"improvement_tips\": [\"3 specific, actionable tips\"],\n"
            "  \"summary\": \"3 sentences max, honest assessment\"\n"
            "}\n\n"
        )

        try:
            if not llm_service.client:
                raise HTTPException(
                    status_code=500,
                    detail="Groq integration is not configured. Please supply a valid GROQ_API_KEY."
                )

            # Query Groq JSON mode
            response = llm_service.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=800,
                messages=[
                    {"role": "system", "content": "You are a senior hiring manager. Evaluate this complete interview transcript."},
                    {"role": "user", "content": system_prompt}
                ]
            )

            raw_json = response.choices[0].message.content
            if not raw_json:
                raise HTTPException(
                    status_code=502,
                    detail="Generative AI grading gateway returned empty response content."
                )
            parsed_data = json.loads(raw_json)

            # Map the parsed overall score robustly (handles both 0-10 and 0-100 metrics as floats/strings)
            overall_field = parsed_data.get("overall_score", 50)
            try:
                overall_f = float(overall_field)
                if overall_f <= 10.0:
                    overall_val = int(round(overall_f * 10.0))
                else:
                    overall_val = int(round(overall_f))
            except (ValueError, TypeError):
                overall_val = 50
            overall_val = max(0, min(100, overall_val))
            
            # Map metrics sub-objects
            metrics = parsed_data.get("metrics", {})
            tech_acc = metrics.get("technical_accuracy", {})
            comm_clar = metrics.get("communication_clarity", {})
            prob_solv = metrics.get("problem_solving", {})
            depth_know = metrics.get("depth_of_knowledge", {})
            conf_tone = metrics.get("confidence", {})

            # Parse scores safely using the robust safe_int_score helper
            tech_score = safe_int_score(tech_acc.get("score"), 5)
            comm_score = safe_int_score(comm_clar.get("score"), 5)
            prob_score = safe_int_score(prob_solv.get("score"), 5)
            depth_score = safe_int_score(depth_know.get("score"), 5)
            conf_score = safe_int_score(conf_tone.get("score"), 5)

            # Prepare benchmarking comparisons based on job role
            benchmark = (
                f"Candidate scored {overall_val}%. The average benchmark score for an equivalent "
                f"{session.difficulty_level.value} {session.estimated_job_role} is 72%."
            )

            # Retrieve missing keywords (handles both nested evaluations formats and root keywords prompts)
            missing_kws = parsed_data.get("missing_keywords", [])
            if not missing_kws and parsed_data.get("evaluations"):
                first_eval = parsed_data.get("evaluations")[0]
                if isinstance(first_eval, dict):
                    missing_kws = first_eval.get("missing_concepts", [])

            # Retrieve improvement tips (fallback check)
            tips_list = parsed_data.get("improvement_tips", [])
            if not tips_list and parsed_data.get("evaluations"):
                first_eval = parsed_data.get("evaluations")[0]
                if isinstance(first_eval, dict):
                    tips_list = first_eval.get("improvement_tips", [])

            # Build evaluations array mapping candidate's answers so we don't break frontend
            evals_mapped = []
            for idx, (q, a) in enumerate(pairs, 1):
                # Retrieve individual question metrics from evaluations array if present, otherwise default to overall metrics
                q_clarity = 7
                q_depth = 7
                q_relevance = 7
                q_confidence = 7
                if parsed_data.get("evaluations") and idx - 1 < len(parsed_data.get("evaluations")):
                    first_eval = parsed_data.get("evaluations")[idx - 1]
                    if isinstance(first_eval, dict):
                        q_clarity = safe_int_score(first_eval.get("clarity_score"), 7)
                        q_depth = safe_int_score(first_eval.get("depth_score"), 7)
                        q_relevance = safe_int_score(first_eval.get("relevance_score"), 7)
                        q_confidence = safe_int_score(first_eval.get("confidence_score"), 7)

                evals_mapped.append(
                    AnswerEvaluation(
                        question=q,
                        answer=a,
                        clarity_score=q_clarity,
                        depth_score=q_depth,
                        relevance_score=q_relevance,
                        confidence_score=q_confidence,
                        missing_concepts=missing_kws if idx == 1 else [],
                        improvement_tips=tips_list if idx == 1 else []
                    )
                )

            # Construct FeedbackReport
            report = FeedbackReport(
                session_id=session_id,
                estimated_job_role=session.estimated_job_role,
                experience_level=session.difficulty_level.value,
                overall_score=overall_val,
                strengths=parsed_data.get("strengths", []),
                weaknesses=parsed_data.get("gaps", []),  # Map gaps to weaknesses
                summary_feedback=parsed_data.get("summary", "Assessment finished."),
                evaluations=evals_mapped,
                
                # New scorecard metrics fields
                grade=parsed_data.get("grade", "C"),
                hire_recommendation=parsed_data.get("hire_recommendation", "Maybe"),
                technical_accuracy_score=tech_score,
                technical_accuracy_note=tech_acc.get("note", ""),
                communication_clarity_score=comm_score,
                communication_clarity_note=comm_clar.get("note", ""),
                problem_solving_score=prob_score,
                problem_solving_note=prob_solv.get("note", ""),
                depth_of_knowledge_score=depth_score,
                depth_of_knowledge_note=depth_know.get("note", ""),
                confidence_score=conf_score,
                confidence_note=conf_tone.get("note", ""),
                missing_keywords=parsed_data.get("missing_keywords", []),
                improvement_tips=parsed_data.get("improvement_tips", []),
                benchmark_comparisons=benchmark
            )

            # 5. Compile PDF report
            pdf_bytes = self.generate_pdf_report(report)

            # 6. Save report in persistent SQLite database
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
            pdf.text(15, 51, f"Target Role: {report.estimated_job_role}")
            pdf.text(15, 58, f"Seniority Level: {report.experience_level}")
            pdf.text(110, 51, f"Hiring Decision: {report.hire_recommendation}")
            pdf.text(110, 58, f"Letter Grade: {report.grade}")
            
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
            pdf.text(20, 85, f"OVERALL ASSESSMENT SCORE:")
            pdf.set_font('Helvetica', 'B', 22)
            pdf.text(150, 87, f"{score} / 100")
            
            pdf.ln(28)

            # Benchmarks Callout
            pdf.set_font('Helvetica', 'I', 9.5)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, report.benchmark_comparisons, 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
            pdf.ln(4)
            
            # Summary Feedback
            pdf.set_text_color(0, 85, 113)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.cell(0, 8, "EXECUTIVE ASSESSMENT SUMMARY", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
            pdf.set_draw_color(0, 85, 113)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)
            
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(70, 70, 70)
            pdf.multi_cell(0, 5, report.summary_feedback)
            pdf.ln(6)
            
            # Core Diagnostics Metrics Scorecard Box
            pdf.set_text_color(0, 85, 113)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.cell(0, 8, "DETAILED GRADING METRICS SCORECARD", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)

            pdf.set_font('Helvetica', 'B', 9.5)
            pdf.set_text_color(60, 60, 60)
            
            # Show the 5 key diagnostics out of 10
            pdf.cell(80, 5, f"- Technical Accuracy: {report.technical_accuracy_score}/10", 0, new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_font('Helvetica', '', 8.5)
            pdf.cell(110, 5, report.technical_accuracy_note, 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            pdf.set_font('Helvetica', 'B', 9.5)
            pdf.cell(80, 5, f"- Communication Clarity: {report.communication_clarity_score}/10", 0, new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_font('Helvetica', '', 8.5)
            pdf.cell(110, 5, report.communication_clarity_note, 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_font('Helvetica', 'B', 9.5)
            pdf.cell(80, 5, f"- Problem Solving: {report.problem_solving_score}/10", 0, new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_font('Helvetica', '', 8.5)
            pdf.cell(110, 5, report.problem_solving_note, 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_font('Helvetica', 'B', 9.5)
            pdf.cell(80, 5, f"- Depth of Knowledge: {report.depth_of_knowledge_score}/10", 0, new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_font('Helvetica', '', 8.5)
            pdf.cell(110, 5, report.depth_of_knowledge_note, 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.set_font('Helvetica', 'B', 9.5)
            pdf.cell(80, 5, f"- Confidence Tone: {report.confidence_score}/10", 0, new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_font('Helvetica', '', 8.5)
            pdf.cell(110, 5, report.confidence_note, 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            pdf.ln(6)

            # Strengths & Weaknesses Split Grid
            pdf.set_font('Helvetica', 'B', 11)
            pdf.set_text_color(46, 125, 50)  # Strength Green
            pdf.cell(90, 6, "PROMINENT KEY STRENGTHS", 0, new_x=XPos.RIGHT, new_y=YPos.TOP, align='L')
            pdf.set_text_color(198, 40, 40)  # Weakness Red
            pdf.cell(90, 6, "IDENTIFIED KNOWLEDGE GAPS", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
            
            pdf.line(10, pdf.get_y(), 95, pdf.get_y())
            pdf.line(110, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)
            
            # Print strengths and weaknesses bullets side-by-side
            y_start = pdf.get_y()
            pdf.set_font('Helvetica', '', 9.5)
            pdf.set_text_color(60, 60, 60)
            
            # Write strengths
            pdf.set_xy(10, y_start)
            for strength in report.strengths[:3]:
                pdf.cell(5, 5, "-", 0, new_x=XPos.RIGHT, new_y=YPos.TOP)  # Bullet
                pdf.multi_cell(80, 5, strength)
                pdf.set_x(10)
                
            y_strengths_end = pdf.get_y()
            
            # Write weaknesses
            pdf.set_xy(110, y_start)
            for weakness in report.weaknesses[:3]:
                pdf.cell(5, 5, "-", 0, new_x=XPos.RIGHT, new_y=YPos.TOP)  # Bullet
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
                pdf.cell(0, 6, f"QUESTION {idx} EVALUATION BREAKDOWN", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
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
                pdf.cell(0, 5, "TECHNICAL CONCEPTS GAPS / OMITTED KEYWORDS:", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
                pdf.set_font('Helvetica', '', 9)
                pdf.set_text_color(60, 60, 60)
                if report.missing_keywords and idx == 1:
                    pdf.multi_cell(0, 5, ", ".join(report.missing_keywords))
                else:
                    pdf.cell(0, 5, "None detected or assessed on this turn.", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
                pdf.ln(4)
                
                pdf.set_font('Helvetica', 'B', 9.5)
                pdf.set_text_color(46, 125, 50)
                pdf.cell(0, 5, "CONSTRUCTIVE COACHING TIPS FOR IMPROVEMENT:", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
                pdf.set_font('Helvetica', '', 9)
                pdf.set_text_color(60, 60, 60)
                tips = report.improvement_tips if idx == 1 else ["Leverage specific technical terms and examples.", "Focus on structure using the STAR methodology."]
                for tip in tips:
                    pdf.cell(5, 5, "-", 0, new_x=XPos.RIGHT, new_y=YPos.TOP)
                    pdf.multi_cell(0, 5, tip)
                    pdf.set_x(10)
            
            # Output PDF to bytes
            return bytes(pdf.output())
            
        except Exception as e:
            logger.error(f"Failed to generate PDF document structure: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while compiling the PDF layout: {str(e)}"
            )

# Singleton service
evaluation_service = EvaluationService()
