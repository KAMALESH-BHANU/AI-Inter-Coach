import json
import os
from typing import Dict, Any, List
from app.config import settings
from app.db.models import GeminiFeedbackModel, ScoreBreakdown, QuestionModel, CandidateAnswerModel
from app.utils.logger import logger

class GeminiService:
    @classmethod
    async def generate_feedback(
        cls, 
        skills: List[str], 
        questions: List[QuestionModel], 
        answers: List[CandidateAnswerModel], 
        scores: ScoreBreakdown
    ) -> GeminiFeedbackModel:
        """
        Generates structured feedback via Gemini API.
        Falls back gracefully to deterministic rule-based feedback if API fails or key is missing.
        """
        if not settings.GEMINI_API_KEY:
            logger.info("Gemini API key not configured. Generating deterministic fallback feedback.")
            return cls._generate_fallback_feedback(skills, scores)

        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            prompt = cls._build_gemini_prompt(skills, questions, answers, scores)
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt
            )

            text_response = response.text.strip()
            # Clean possible markdown code fences
            if text_response.startswith("```json"):
                text_response = text_response[7:]
            if text_response.endswith("```"):
                text_response = text_response[:-3]

            parsed_json = json.loads(text_response.strip())
            return GeminiFeedbackModel(
                overall_summary=parsed_json.get("overall_summary", "Completed mock interview session."),
                strengths=parsed_json.get("strengths", ["Strong overall performance."]),
                areas_to_improve=parsed_json.get("areas_to_improve", ["Practice technical depth."]),
                technical_strengths=parsed_json.get("technical_strengths", []),
                communication_strengths=parsed_json.get("communication_strengths", []),
                technical_improvements=parsed_json.get("technical_improvements", []),
                communication_improvements=parsed_json.get("communication_improvements", []),
                project_feedback=parsed_json.get("project_feedback", []),
                specific_suggestions=parsed_json.get("specific_suggestions", []),
                recommended_topics=parsed_json.get("recommended_topics", []),
                interview_readiness=parsed_json.get("interview_readiness", "Ready for Interviews"),
                final_feedback=parsed_json.get("final_feedback", "Solid technical foundation demonstrated."),
                is_fallback=False
            )

        except Exception as e:
            logger.warning(f"Gemini API request failed ({e}). Returning deterministic fallback feedback.")
            return cls._generate_fallback_feedback(skills, scores)

    @classmethod
    def _build_gemini_prompt(cls, skills: List[str], questions: List[QuestionModel], answers: List[CandidateAnswerModel], scores: ScoreBreakdown) -> str:
        q_summary = []
        for i, q in enumerate(questions):
            ans = answers[i] if i < len(answers) else None
            q_summary.append({
                "question_number": i + 1,
                "type": q.type,
                "skill": q.skill,
                "question": q.question,
                "candidate_answer": ans.transcript if ans else "No response",
                "technical_score": ans.technical_score if ans else 0.0,
                "eye_contact": ans.eye_contact_pct if ans else 0.0,
                "wpm": ans.wpm if ans else 0.0,
                "filler_count": ans.filler_count if ans else 0
            })

        return f"""
You are an expert AI Technical Interview Coach evaluating a candidate's mock interview performance.
Candidate Primary Skills: {', '.join(skills)}

Interview Performance Summary:
- Overall Score: {scores.overall_score}/100
- Technical Knowledge: {scores.technical_knowledge}/100
- Answer Quality: {scores.answer_quality}/100
- Communication: {scores.communication}/100
- Project Understanding: {scores.project_understanding}/100
- Presentation & Eye Contact: {scores.presentation}/100 (Avg Eye Contact: {scores.eye_contact}%)
- Speech Fluency: {scores.speech_fluency}/100

Questions and Candidate Responses:
{json.dumps(q_summary, indent=2)}

Output ONLY valid JSON with this exact schema:
{{
  "overall_summary": "Concise high-level summary of performance",
  "strengths": ["Key strength 1", "Key strength 2"],
  "areas_to_improve": ["Improvement area 1", "Improvement area 2"],
  "technical_strengths": ["Technical strength 1"],
  "communication_strengths": ["Communication strength 1"],
  "technical_improvements": ["Technical concept to refine"],
  "communication_improvements": ["Communication tip"],
  "project_feedback": ["Feedback on project ownership/answers"],
  "specific_suggestions": ["Actionable study tip 1", "Actionable study tip 2"],
  "recommended_topics": ["Topic 1", "Topic 2"],
  "interview_readiness": "Needs Practice | Almost Ready | Interview Ready | Exceptional",
  "final_feedback": "Encouraging final closing remarks"
}}
"""

    @classmethod
    def _generate_fallback_feedback(cls, skills: List[str], scores: ScoreBreakdown) -> GeminiFeedbackModel:
        overall = scores.overall_score
        
        readiness = "Needs Practice"
        if overall >= 85:
            readiness = "Exceptional"
        elif overall >= 75:
            readiness = "Interview Ready"
        elif overall >= 60:
            readiness = "Almost Ready"

        strengths = []
        if scores.technical_knowledge >= 70:
            strengths.append("Solid grasp of core technical concepts and syntax.")
        if scores.communication >= 70:
            strengths.append("Clear articulation with steady pace and good flow.")
        if scores.eye_contact >= 70:
            strengths.append("Maintained strong eye contact and professional camera engagement.")
        if not strengths:
            strengths.append("Completed all 10 interview questions diligently.")

        improvements = []
        if scores.technical_knowledge < 70:
            improvements.append("Elaborate further on architectural trade-offs and expected concepts.")
        if scores.communication < 70:
            improvements.append("Reduce filler word frequency and regulate speaking pace.")
        if scores.eye_contact < 70:
            improvements.append("Align webcam at eye-level and focus toward the lens when answering.")
        if not improvements:
            improvements.append("Refine pseudocode tracing speed under timed conditions.")

        return GeminiFeedbackModel(
            overall_summary=f"Candidate achieved an overall score of {overall}/100 across 10 interview questions.",
            strengths=strengths,
            areas_to_improve=improvements,
            technical_strengths=[f"Demonstrated competence in {s}" for s in skills[:2]],
            communication_strengths=["Pacing was clear throughout the session."],
            technical_improvements=["Deepen knowledge of system design and edge cases."],
            communication_improvements=["Practice structuring answers using the STAR method."],
            project_feedback=["Clearly state individual contributions when discussing project architecture."],
            specific_suggestions=["Review data structures complexity", "Practice mock interviews under timed conditions"],
            recommended_topics=skills[:3] + ["System Design", "Algorithms"],
            interview_readiness=readiness,
            final_feedback="Good effort! Focus on strengthening technical depth and maintaining consistent eye contact.",
            is_fallback=True
        )
