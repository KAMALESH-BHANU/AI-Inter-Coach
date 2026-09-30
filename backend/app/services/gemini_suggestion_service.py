import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.config import settings
from app.db.models import InterviewSessionModel, QuestionType, QuestionModel, CandidateAnswerModel
from app.schemas.suggestion_schema import (
    CommunicationFeedback,
    TechnicalFeedbackItem,
    QuestionWiseFeedback,
    PracticePlanItem,
    GeminiSuggestionResponse,
    InterviewAnalysisPayload,
    CandidateProfilePayload,
    ScoreSummaryPayload,
    CommunicationMetricsPayload,
    QuestionResultPayload
)
from app.utils.logger import logger

class GeminiSuggestionService:
    @classmethod
    def build_analysis_payload(cls, session: InterviewSessionModel) -> Dict[str, Any]:
        """
        Separate mapping layer that converts existing interview session into
        a compact, privacy-compliant, isolated analysis payload for Gemini.
        Strictly prevents sensitive data leakage and enforces answer-type isolation.
        """
        skills = session.skills or ["General Software Engineering"]
        projects_payload = []
        for p in (session.projects or []):
            if isinstance(p, dict):
                p_name = p.get("name") or p.get("title")
                if p_name:
                    projects_payload.append({
                        "name": str(p_name),
                        "techStack": p.get("technologies", []) or p.get("skills", [])
                    })

        profile = CandidateProfilePayload(
            skills=skills,
            projects=projects_payload,
            targetRole="Software Engineer"
        )

        scores = session.scores
        answered_count = len([a for a in session.answers if getattr(a, 'status', 'ANSWERED') != 'NOT_ANSWERED'])
        score_summary = ScoreSummaryPayload(
            totalQuestions=len(session.questions) or 13,
            answeredQuestions=answered_count,
            overallScore=scores.overall_score if scores else 0.0,
            speechScore=scores.speech_fluency if scores else 0.0,
            technicalScore=scores.technical_knowledge if scores else 0.0,
            pseudocodeScore=scores.pseudocode_score if scores else 0.0,
            sqlScore=scores.sql_score if scores else 0.0
        )

        speech = session.speech_metrics
        vision = session.vision_metrics
        fm = vision.face_monitoring if vision else None

        comm_metrics = CommunicationMetricsPayload(
            eyeContactPercentage=vision.average_eye_contact_pct if vision else (scores.eye_contact if scores else 0.0),
            wordsPerMinute=speech.average_wpm if speech else 0.0,
            fillerWordCount=speech.total_fillers if speech else 0,
            pauseCount=sum(a.pause_count for a in session.answers),
            faceMissingEvents=fm.missing_face_events if fm else 0,
            multipleFaceEvents=fm.multiple_face_events if fm else 0,
            faceStatusSummary="Normal Single Face" if (fm and fm.single_face_percentage >= 85.0) else "Check Camera Position"
        )

        q_results: List[QuestionResultPayload] = []
        for idx, q in enumerate(session.questions):
            ans = session.answers[idx] if idx < len(session.answers) else None
            q_num = idx + 1
            q_type_str = str(q.type).lower()

            if q_type_str in ["sql", "questiontype.sql"]:
                # Q12-Q13: SQL Question (Query and SQL evaluation only)
                c_query = None
                if ans:
                    c_query = ans.candidate_query or (ans.transcript if ans.transcript and not ans.transcript.startswith("-- Write your MySQL") and not ans.transcript.startswith("SELECT * FROM Products;") and ans.transcript != "SQL Query Submitted" else None)
                if not c_query:
                    c_query = "No query submitted"

                eval_notes = ""
                if ans:
                    if ans.is_correct:
                        eval_notes = "SQL query executed successfully and matched expected schema and rows."
                    elif ans.execution_error:
                        eval_notes = f"SQL execution error: {ans.execution_error}"
                    else:
                        eval_notes = "SQL query returned mismatched results or columns compared to expected output."

                q_results.append(QuestionResultPayload(
                    questionNumber=q_num,
                    questionType="SQL",
                    skill=q.skill or "MySQL",
                    topic=q.topic or "Relational Databases",
                    question=q.question,
                    candidateTranscript=None,
                    selectedOption=None,
                    candidateQuery=c_query,
                    isCorrect=ans.is_correct if ans else False,
                    score=ans.technical_score if ans else 0.0,
                    maxScore=100.0,
                    missingConcepts=[],
                    evaluationNotes=eval_notes
                ))

            elif q_type_str in ["pseudocode", "pseudocode_mcq", "questiontype.pseudocode", "questiontype.pseudocode_mcq"]:
                # Q10-Q11: Pseudocode MCQ (Option and correctness only)
                sel_opt = None
                if ans:
                    sel_opt = ans.selected_option_id or ans.selected_option
                if not sel_opt:
                    sel_opt = "Not answered"

                eval_notes = ""
                if ans:
                    if ans.is_correct:
                        eval_notes = f"Correct option {sel_opt} selected."
                    else:
                        corr = q.correctOptionId or q.correct_option_id or q.correct_answer or "A"
                        eval_notes = f"Selected {sel_opt}; correct answer was {corr}."

                q_results.append(QuestionResultPayload(
                    questionNumber=q_num,
                    questionType="PSEUDOCODE_MCQ",
                    skill=q.skill or "Logic and Algorithms",
                    topic=q.topic or "Algorithm Tracing",
                    question=q.question,
                    candidateTranscript=None,
                    selectedOption=sel_opt,
                    candidateQuery=None,
                    isCorrect=ans.is_correct if ans else False,
                    score=ans.technical_score if ans else 0.0,
                    maxScore=1.0,
                    missingConcepts=[],
                    evaluationNotes=eval_notes
                ))

            else:
                # Q1-Q9: Spoken questions (Speech transcript only)
                raw_trans = (ans.transcript if ans else "") or ""
                # Strict sanitization: never send SQL placeholders as speech
                if raw_trans.startswith("-- Write your MySQL") or raw_trans.startswith("SELECT * FROM Products;") or raw_trans == "SQL Query Submitted":
                    raw_trans = ""
                
                trans_val = raw_trans.strip() if len(raw_trans.strip()) > 0 else "No spoken response recorded"
                eval_notes = ""
                if ans:
                    if ans.technical_score >= 80:
                        eval_notes = "Strong conceptual clarity and relevant technical depth."
                    elif ans.technical_score >= 50:
                        eval_notes = "Basic concepts covered; could elaborate on architectural trade-offs."
                    else:
                        eval_notes = "Limited coverage of expected core technical concepts."

                q_type_label = "INTRODUCTION" if q_type_str in ["introduction", "questiontype.introduction"] else ("PROJECT" if q_type_str in ["project", "questiontype.project"] else "TECHNICAL")

                q_results.append(QuestionResultPayload(
                    questionNumber=q_num,
                    questionType=q_type_label,
                    skill=q.skill or "General",
                    topic=q.topic or "Core Concepts",
                    question=q.question,
                    candidateTranscript=trans_val,
                    selectedOption=None,
                    candidateQuery=None,
                    isCorrect=None,
                    score=ans.technical_score if ans else 0.0,
                    maxScore=100.0,
                    missingConcepts=getattr(q, 'expected_concepts', [])[:3] if (ans and ans.technical_score < 70) else [],
                    evaluationNotes=eval_notes
                ))

        payload = InterviewAnalysisPayload(
            candidateProfile=profile,
            scoreSummary=score_summary,
            communicationMetrics=comm_metrics,
            questionResults=q_results
        )

        return payload.model_dump(by_alias=True)

    @classmethod
    def _clean_json_response(cls, text: str) -> str:
        """Strips Markdown code fences and whitespace from LLM response."""
        t = text.strip()
        if t.startswith("```json"):
            t = t[7:]
        elif t.startswith("```"):
            t = t[3:]
        if t.endswith("```"):
            t = t[:-3]
        return t.strip()

    @classmethod
    def _build_prompt(cls, payload: Dict[str, Any]) -> str:
        return f"""You are an elite, encouraging AI Interview Coach providing constructive post-interview feedback for a candidate.

CRITICAL COACHING RULES:
1. The backend objective scores and metrics provided below are authoritative. Do NOT recalculate or contradict them.
2. Do NOT judge candidate appearance, age, gender, accent, ethnicity, or personal identity.
3. Do NOT make hiring/firing or employment decisions. Act strictly as a skill-building coach.
4. Separate technical feedback from behavioral and communication feedback.
5. Respect question isolation:
   - Q1-Q9: Evaluate based on spoken transcript.
   - Q10-Q11: Evaluate based on MCQ option and correctness.
   - Q12-Q13: Evaluate based on submitted SQL query and database execution result.
6. Provide specific, practical advice. Avoid generic filler statements.

OUTPUT LIMITS & FORMAT:
- Return ONLY a valid JSON object matching the requested schema.
- strengths: maximum 5 items.
- improvementAreas: maximum 5 items.
- technicalFeedback: maximum 8 items.
- questionWiseFeedback: maximum 13 items (one per question).
- recommendedTopics: maximum 8 items.
- practicePlan: EXACTLY 5 items (Day 1, Day 2, Day 3, Day 4, Day 5).
- nextInterviewGoals: maximum 5 items.

INTERVIEW ANALYSIS PAYLOAD:
{json.dumps(payload, indent=2)}

Produce ONLY valid JSON with this exact schema:
{{
  "overallSummary": "Concise 2-3 paragraph holistic executive coaching summary.",
  "strengths": ["Strength 1", "Strength 2", "Strength 3"],
  "improvementAreas": ["Area 1", "Area 2", "Area 3"],
  "communicationFeedback": {{
    "eyeContact": "Specific assessment of eye contact and camera engagement.",
    "speakingPace": "Pace feedback regarding WPM and cadence.",
    "fillerWords": "Observation on filler word frequency and tips to reduce.",
    "pauses": "Feedback on thinking pauses and response fluency.",
    "clarity": "Feedback on message articulation and answer structuring."
  }},
  "technicalFeedback": [
    {{
      "topic": "Topic name",
      "observation": "What the candidate demonstrated",
      "recommendation": "How to level up this technical skill"
    }}
  ],
  "questionWiseFeedback": [
    {{
      "questionNumber": 1,
      "feedback": "Feedback on question answer",
      "improvementSuggestion": "Concrete suggestion for this question"
    }}
  ],
  "recommendedTopics": ["Topic 1", "Topic 2", "Topic 3"],
  "practicePlan": [
    {{
      "day": 1,
      "focus": "Day 1 Focus Domain",
      "tasks": ["Task 1", "Task 2"]
    }},
    {{
      "day": 2,
      "focus": "Day 2 Focus Domain",
      "tasks": ["Task 1", "Task 2"]
    }},
    {{
      "day": 3,
      "focus": "Day 3 Focus Domain",
      "tasks": ["Task 1", "Task 2"]
    }},
    {{
      "day": 4,
      "focus": "Day 4 Focus Domain",
      "tasks": ["Task 1", "Task 2"]
    }},
    {{
      "day": 5,
      "focus": "Day 5 Focus Domain",
      "tasks": ["Task 1", "Task 2"]
    }}
  ],
  "nextInterviewGoals": ["Goal 1", "Goal 2", "Goal 3"]
}}
"""

    @classmethod
    async def generate_interview_suggestions(cls, interview_summary: Dict[str, Any]) -> GeminiSuggestionResponse:
        """
        Calls Gemini using google-genai SDK, validates against Pydantic schema,
        handles 1-shot retry on invalid JSON, and returns a safe fallback on any failure.
        """
        if not settings.is_gemini_configured():
            logger.info("Gemini API key is not configured. Returning deterministic fallback suggestions.")
            return cls.generate_deterministic_fallback(interview_summary, fallback_reason="GEMINI_API_KEY is not configured in backend environment variables.")

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = cls._build_prompt(interview_summary)

            models_to_try = [
                settings.GEMINI_MODEL,
                "gemini-3.8-flash",
                "gemini-3.5-flash-lite",
                "gemini-3.5-flash",
                "gemini-flash-latest"
            ]
            models_to_try = list(dict.fromkeys(models_to_try))

            response = None
            last_err = None
            used_model = settings.GEMINI_MODEL

            for model_name in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
                            temperature=0.3
                        )
                    )
                    if response and response.text:
                        used_model = model_name
                        break
                except Exception as m_err:
                    logger.warning(f"Gemini model '{model_name}' attempt failed ({m_err}). Trying next candidate...")
                    last_err = m_err

            if not response or not response.text:
                raise last_err or Exception("All Gemini model candidates failed to return response.")

            raw_text = response.text or ""
            clean_text = cls._clean_json_response(raw_text)

            parsed = None
            try:
                parsed = json.loads(clean_text)
            except Exception as json_err:
                logger.warning(f"Initial JSON parse failed ({json_err}). Triggering 1-shot retry...")
                retry_prompt = f"Your previous output was invalid JSON ({json_err}). Fix and return ONLY valid JSON matching the exact schema:\n\n{clean_text[:1500]}"
                retry_resp = client.models.generate_content(
                    model=used_model,
                    contents=retry_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
                        temperature=0.1
                    )
                )
                clean_retry = cls._clean_json_response(retry_resp.text or "")
                parsed = json.loads(clean_retry)

            # Clamp array bounds to enforced limits
            parsed["strengths"] = (parsed.get("strengths") or [])[:5]
            parsed["improvementAreas"] = (parsed.get("improvementAreas") or [])[:5]
            parsed["technicalFeedback"] = (parsed.get("technicalFeedback") or [])[:8]
            parsed["questionWiseFeedback"] = (parsed.get("questionWiseFeedback") or [])[:13]
            parsed["recommendedTopics"] = (parsed.get("recommendedTopics") or [])[:8]
            parsed["nextInterviewGoals"] = (parsed.get("nextInterviewGoals") or [])[:5]

            # Enforce exactly 5 practice plan days
            p_plan = parsed.get("practicePlan") or []
            if len(p_plan) < 5:
                fallback_plan = cls._generate_default_practice_plan(interview_summary)
                for day_idx in range(len(p_plan) + 1, 6):
                    p_plan.append(fallback_plan[day_idx - 1])
            parsed["practicePlan"] = p_plan[:5]
            parsed["isFallback"] = False
            parsed["fallbackReason"] = None
            parsed["generatedAt"] = datetime.utcnow()

            validated_res = GeminiSuggestionResponse.model_validate(parsed)
            logger.info("Successfully generated and validated Gemini AI interview suggestions.")
            return validated_res

        except Exception as e:
            logger.warning(f"Gemini Suggestion Service encountered an issue ({e}). Returning deterministic fallback.")
            return cls.generate_deterministic_fallback(
                interview_summary,
                fallback_reason=f"Gemini API request failed ({type(e).__name__}). Using deterministic offline coaching rules."
            )

    @classmethod
    def _generate_default_practice_plan(cls, summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        skills = summary.get("candidateProfile", {}).get("skills", ["Core Technical Skills"])
        s1 = skills[0] if len(skills) > 0 else "Data Structures"
        s2 = skills[1] if len(skills) > 1 else "System Design"
        s3 = skills[2] if len(skills) > 2 else "Database Queries"

        return [
            {"day": 1, "focus": f"{s1} Deep-Dive & Architecture", "tasks": [f"Review core runtime models and memory management in {s1}", "Implement 2 classic coding patterns without IDE autocomplete"]},
            {"day": 2, "focus": f"{s2} & Concurrency Handling", "tasks": [f"Study multithreading, async lifecycles, and synchronization in {s2}", "Practice explaining complex design trade-offs aloud using the STAR method"]},
            {"day": 3, "focus": f"{s3} & SQL Optimization", "tasks": ["Write 5 complex queries involving subqueries, aggregate grouping, and index tuning", "Analyze execution plans and join complexity"]},
            {"day": 4, "focus": "Algorithm Tracing & Pseudocode Logic", "tasks": ["Trace 5 multi-branch loop and recursion scenarios manually on paper", "Calculate time and space complexity for search and sort routines"]},
            {"day": 5, "focus": "Full Behavioral & Timed Mock Interview", "tasks": ["Record a 2-minute introduction focusing on direct impact and key metrics", "Conduct a timed 13-question mock session maintaining consistent eye contact"]}
        ]

    @classmethod
    def generate_deterministic_fallback(cls, summary: Dict[str, Any], fallback_reason: str = "Offline Mode") -> GeminiSuggestionResponse:
        """
        Generates robust, deterministic, rule-based feedback derived from
        the candidate's actual score breakdown and communication metrics.
        """
        scores = summary.get("scoreSummary", {})
        overall = scores.get("overallScore", 70.0)
        tech_score = scores.get("technicalScore", 70.0)
        speech_score = scores.get("speechScore", 70.0)
        sql_score = scores.get("sqlScore", 100.0)
        pseudo_score = scores.get("pseudocodeScore", 100.0)

        comm = summary.get("communicationMetrics", {})
        eye_pct = comm.get("eyeContactPercentage", 75.0)
        wpm = comm.get("wordsPerMinute", 130.0)
        fillers = comm.get("fillerWordCount", 2)

        skills = summary.get("candidateProfile", {}).get("skills", ["Core Technical Skills"])
        s_main = skills[0] if skills else "Software Engineering"

        strengths = []
        if tech_score >= 70:
            strengths.append(f"Solid foundational knowledge demonstrated across {s_main} and key technical domains.")
        if eye_pct >= 75:
            strengths.append(f"Strong camera engagement with an average eye contact rate of {eye_pct}%.")
        if sql_score == 100:
            strengths.append("Flawless execution on relational database and SQL queries.")
        if pseudo_score == 100:
            strengths.append("Excellent algorithm tracing and logical output prediction on pseudocode questions.")
        if not strengths:
            strengths.append("Completed all 13 questions across project, technical, logic, and SQL sections.")

        improvements = []
        if tech_score < 75:
            improvements.append("Elaborate further on architectural trade-offs, internal mechanics, and error handling.")
        if eye_pct < 70:
            improvements.append("Position camera at eye level and maintain deliberate focus on the lens when speaking.")
        if wpm < 110 or wpm > 160:
            improvements.append(f"Regulate speaking pace toward the optimal range of 120-150 WPM (current: {wpm} WPM).")
        if fillers > 4:
            improvements.append(f"Reduce filler word count (current: {fillers}) by embracing brief, silent pauses.")
        if not improvements:
            improvements.append("Refine real-time code explanation speed and practice answering edge cases proactively.")

        comm_fb = CommunicationFeedback(
            eyeContact=f"Maintained {eye_pct}% camera gaze. " + ("Optimal camera presence!" if eye_pct >= 75 else "Aim for >75% by looking directly at the camera."),
            speakingPace=f"Speaking rate was {wpm} WPM. " + ("Ideal conversational pace (120-150 WPM)." if 115 <= wpm <= 155 else "Adjust pace toward 130 WPM for maximum clarity."),
            fillerWords=f"Detected {fillers} filler words. " + ("Excellent vocal discipline." if fillers <= 3 else "Replace filler sounds with deliberate silent pauses."),
            pauses="Pauses were well-measured before structuring multi-part technical explanations.",
            clarity="Clear sentence structure with structured articulation throughout the session."
        )

        tech_items = [
            TechnicalFeedbackItem(
                topic=s_main,
                observation=f"Demonstrated practical familiarity with {s_main} principles and application architecture.",
                recommendation=f"Review advanced internals, concurrency controls, and performance profiling for {s_main}."
            ),
            TechnicalFeedbackItem(
                topic="Database & Query Optimization",
                observation="Handled relational schema navigation and SQL constraints accurately.",
                recommendation="Practice complex multi-table joins, window functions, and indexing strategies."
            )
        ]

        q_fb = []
        for q in summary.get("questionResults", [])[:13]:
            q_num = q.get("questionNumber", 1)
            q_type = q.get("questionType", "TECHNICAL")
            score = q.get("score", 0.0)

            if score >= 75:
                fb_text = f"Strong answer on {q_type.lower()} question with clear logic and accurate terminology."
                sug_text = "Maintain this level of concise technical depth."
            elif score >= 50:
                fb_text = f"Satisfactory answer covering core points; could benefit from deeper conceptual context."
                sug_text = "Structure answers using Context -> Action -> Result -> Trade-off."
            else:
                fb_text = f"Answer was incomplete or missed expected core concepts on {q_type.lower()} question."
                sug_text = "Review standard reference documentation and practice vocalizing the solution step-by-step."

            q_fb.append(QuestionWiseFeedback(
                questionNumber=q_num,
                feedback=fb_text,
                improvementSuggestion=sug_text
            ))

        practice_plan_raw = cls._generate_default_practice_plan(summary)
        practice_plan_items = [PracticePlanItem(**d) for d in practice_plan_raw]

        return GeminiSuggestionResponse(
            overallSummary=f"Candidate completed a comprehensive 13-question technical interview session with an overall objective score of {overall}/100. Strengths were demonstrated in {s_main} and analytical problem-solving. Following the structured 5-day practice plan will solidify interview readiness.",
            strengths=strengths[:5],
            improvementAreas=improvements[:5],
            communicationFeedback=comm_fb,
            technicalFeedback=tech_items[:8],
            questionWiseFeedback=q_fb[:13],
            recommendedTopics=skills[:5] + ["System Architecture", "SQL Optimization"],
            practicePlan=practice_plan_items,
            nextInterviewGoals=[
                "Maintain >80% camera eye contact consistently across all questions",
                "Structure all technical answers with clear modular architecture and trade-offs",
                f"Achieve >=85% on technical questions in {s_main}",
                "Solve both SQL coding challenges with 100% test case accuracy"
            ],
            isFallback=True,
            fallbackReason=fallback_reason,
            generatedAt=datetime.utcnow()
        )
