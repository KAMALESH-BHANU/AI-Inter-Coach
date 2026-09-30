import re
from typing import List, Dict, Any, Optional
from app.db.models import QuestionModel, CandidateAnswerModel, ScoreBreakdown, QuestionType
from app.utils.logger import logger

from app.services.sql_service import SqlService

class ScoringService:
    @classmethod
    def evaluate_single_answer(
        cls,
        question: Optional[QuestionModel] = None,
        transcript: str = "",
        metrics: Optional[Dict[str, Any]] = None,
        selected_option: Optional[str] = None,
        **kwargs
    ) -> Dict[str, float]:
        """
        Evaluates a single answer deterministically.
        If candidate spoke nothing or gave no answer, score is strictly 0.0.
        """
        if metrics is None:
            metrics = {}

        # Merge any extra kwargs
        for k, v in kwargs.items():
            if k not in metrics:
                metrics[k] = v

        if not question:
            return {"technical_score": 0.0, "quality_score": 0.0, "communication_score": 0.0}

        clean_text = (transcript or "").strip()
        has_spoken = len(clean_text) >= 5 and clean_text.lower() != "candidate answered."

        # 1. Evaluate SQL questions directly
        if question.type == QuestionType.SQL:
            candidate_query = (metrics.get("candidate_query") or clean_text or "").strip()
            is_correct = metrics.get("is_correct")

            if is_correct is None and candidate_query and question.tables and question.expected_query:
                eval_res = SqlService.evaluate_sql_answer(
                    question.tables,
                    candidate_query,
                    question.expected_query
                )
                is_correct = eval_res.get("is_correct", False)

            if is_correct:
                return {
                    "technical_score": 100.0,
                    "quality_score": 100.0,
                    "communication_score": 100.0
                }
            elif candidate_query and len(candidate_query) >= 5:
                # Query was attempted
                return {
                    "technical_score": 40.0,
                    "quality_score": 40.0,
                    "communication_score": 50.0
                }
            else:
                return {
                    "technical_score": 0.0,
                    "quality_score": 0.0,
                    "communication_score": 0.0
                }

        # 2. Evaluate Pseudocode MCQ questions (Objective option selection)
        if question.type in [QuestionType.PSEUDOCODE, QuestionType.PSEUDOCODE_MCQ]:
            selected = selected_option or metrics.get("selected_option_id") or metrics.get("selected_option")
            correct_opt = question.correctOptionId or question.correct_option_id or question.correct_answer

            if selected:
                selected_clean = str(selected).strip().lower()
                correct_clean = str(correct_opt).strip().lower() if correct_opt else ""
                is_correct = (selected_clean == correct_clean)
                
                # Also check matching against option texts if option object was sent
                if not is_correct and question.options:
                    for opt in question.options:
                        if isinstance(opt, dict):
                            if str(opt.get("id", "")).strip().lower() == selected_clean and str(opt.get("id", "")).strip().lower() == correct_clean:
                                is_correct = True
                            elif str(opt.get("text", "")).strip().lower() == selected_clean:
                                if str(opt.get("id", "")).strip().lower() == correct_clean or str(opt.get("text", "")).strip().lower() == correct_clean:
                                    is_correct = True
                
                tech_score = 100.0 if is_correct else 0.0
                return {
                    "technical_score": tech_score,
                    "quality_score": tech_score,
                    "communication_score": tech_score,
                    "is_correct": is_correct
                }
            else:
                return {
                    "technical_score": 0.0,
                    "quality_score": 0.0,
                    "communication_score": 0.0,
                    "is_correct": False
                }

        # 3. Evaluate Introduction, Technical & Project questions via Concept Matching
        if not has_spoken:
            return {
                "technical_score": 0.0,
                "quality_score": 0.0,
                "communication_score": 0.0
            }

        transcript_lower = clean_text.lower()
        matched_concepts = 0
        total_concepts = max(len(question.expected_concepts), 1)

        for concept in question.expected_concepts:
            concept_words = concept.lower().split()
            if all(w in transcript_lower for w in concept_words):
                matched_concepts += 1
            elif concept.lower() in transcript_lower:
                matched_concepts += 1

        concept_ratio = matched_concepts / total_concepts
        word_count = len(clean_text.split())

        # Technical score based on concept coverage and relevant depth
        tech_score = round(min(100.0, (concept_ratio * 80.0) + min(20.0, word_count * 0.4)), 1)

        # Quality score based on explanation completeness
        quality_score = round(min(100.0, (concept_ratio * 75.0) + min(25.0, word_count * 0.5)), 1)

        # Communication score based on WPM and filler word frequency
        wpm = metrics.get("wpm", 0.0)
        filler_count = metrics.get("filler_count", 0)

        if wpm <= 0 or word_count < 3:
            comm_score = 0.0
        else:
            wpm_score = 100.0
            if wpm < 80:
                wpm_score = max(40.0, 100.0 - (80 - wpm) * 1.5)
            elif wpm > 180:
                wpm_score = max(40.0, 100.0 - (wpm - 180) * 1.5)

            filler_penalty = min(50.0, filler_count * 6.0)
            comm_score = round(max(20.0, wpm_score - filler_penalty), 1)

        return {
            "technical_score": tech_score,
            "quality_score": quality_score,
            "communication_score": comm_score
        }

    # Clean unified evaluate_answer interface
    @classmethod
    def evaluate_answer(
        cls,
        question: Optional[QuestionModel] = None,
        answer_transcript: str = "",
        transcript: str = "",
        selected_option: Optional[str] = None,
        **kwargs
    ) -> Dict[str, float]:
        text = answer_transcript or transcript or ""
        return cls.evaluate_single_answer(
            question=question,
            transcript=text,
            selected_option=selected_option,
            metrics=kwargs
        )

    @classmethod
    def aggregate_session_scores(cls, questions: List[QuestionModel], answers: List[CandidateAnswerModel]) -> ScoreBreakdown:
        if not answers:
            return ScoreBreakdown()

        tech_scores = []
        quality_scores = []
        comm_scores = []
        project_scores = []
        pseudo_scores = []
        sql_correct_count = 0
        sql_total_count = 0

        total_eye_contact = 0.0
        total_wpm = 0.0
        total_fillers = 0
        answered_count = 0

        for i, q in enumerate(questions):
            ans = next((a for a in answers if a.question_id == q.id or a.question_index == i), None)
            if not ans and i < len(answers):
                ans = answers[i]

            if not ans:
                continue

            if q.type == QuestionType.SQL:
                clean_text = (ans.candidate_query or (ans.transcript if ans.transcript != 'SQL Query Submitted' else '') or "").strip()
                is_valid_ans = len(clean_text) >= 3 or ans.is_correct is True or ans.technical_score > 0
            elif q.type in [QuestionType.PSEUDOCODE, QuestionType.PSEUDOCODE_MCQ]:
                is_valid_ans = (ans.selected_option is not None and str(ans.selected_option).strip() != "") or ans.technical_score > 0
            else:
                clean_text = (ans.transcript or "").strip()
                if clean_text.startswith("-- Write your MySQL query"):
                    clean_text = ""
                is_valid_ans = (len(clean_text) >= 3 and clean_text.lower() != "candidate answered.") or ans.technical_score > 0 or ans.communication_score > 0

            if is_valid_ans:
                answered_count += 1

            tech_scores.append(ans.technical_score or 0.0)
            quality_scores.append(ans.quality_score or 0.0)
            comm_scores.append(ans.communication_score or 0.0)

            if q.type == QuestionType.PROJECT:
                project_scores.append(ans.technical_score or 0.0)
            elif q.type in [QuestionType.PSEUDOCODE, QuestionType.PSEUDOCODE_MCQ]:
                pseudo_scores.append(ans.technical_score or 0.0)
            elif q.type == QuestionType.SQL:
                sql_total_count += 1
                if ans.is_correct:
                    sql_correct_count += 1

            if ans.eye_contact_pct > 0:
                total_eye_contact += ans.eye_contact_pct
            total_wpm += ans.wpm
            total_fillers += ans.filler_count

        total_q = max(len(questions), len(answers), 1)

        avg_tech = round(sum(tech_scores) / total_q, 1) if tech_scores else 0.0
        avg_quality = round(sum(quality_scores) / total_q, 1) if quality_scores else 0.0
        avg_comm = round(sum(comm_scores) / total_q, 1) if comm_scores else 0.0
        avg_project = round(sum(project_scores) / max(len(project_scores), 1), 1) if project_scores else 0.0
        avg_pseudo = round(sum(pseudo_scores) / max(len(pseudo_scores), 1), 1) if pseudo_scores else 0.0

        # Exact formula: (Correct SQL Answers / 2) * 100
        sql_score = round((sql_correct_count / max(sql_total_count, 2.0)) * 100.0, 1)

        valid_eye_count = sum(1 for a in answers if a.eye_contact_pct > 0)
        avg_eye_contact = round(total_eye_contact / max(valid_eye_count, 1), 1) if valid_eye_count > 0 else 85.0
        avg_wpm = round(total_wpm / max(len(answers), 1), 1) if answers else 0.0

        # If candidate answered nothing across all questions, overall score is strictly 0.0
        if answered_count == 0 and avg_tech == 0.0 and avg_comm == 0.0 and sql_score == 0.0:
            return ScoreBreakdown(
                technical_knowledge=0.0,
                answer_quality=0.0,
                communication=0.0,
                project_understanding=0.0,
                presentation=0.0,
                eye_contact=avg_eye_contact,
                speech_fluency=0.0,
                pseudocode_score=0.0,
                sql_score=sql_score,
                overall_score=0.0
            )

        presentation_score = round(min(100.0, avg_eye_contact), 1)
        filler_penalty_total = min(40.0, total_fillers * 3.0)
        speech_fluency = round(max(0.0, 100.0 - filler_penalty_total), 1)

        # Weighted Overall Score (Technical, Quality, Communication, Project, Presentation, SQL)
        overall = (
            0.35 * avg_tech +
            0.20 * avg_quality +
            0.15 * avg_comm +
            0.10 * avg_project +
            0.05 * presentation_score +
            0.15 * sql_score
        )

        return ScoreBreakdown(
            technical_knowledge=avg_tech,
            answer_quality=avg_quality,
            communication=avg_comm,
            project_understanding=avg_project,
            presentation=presentation_score,
            eye_contact=avg_eye_contact,
            speech_fluency=speech_fluency,
            pseudocode_score=avg_pseudo,
            sql_score=sql_score,
            overall_score=round(overall, 1)
        )

    # Alias for backwards compatibility
    @classmethod
    def calculate_session_scores(cls, questions: List[QuestionModel], answers: List[CandidateAnswerModel]) -> ScoreBreakdown:
        return cls.aggregate_session_scores(questions, answers)
