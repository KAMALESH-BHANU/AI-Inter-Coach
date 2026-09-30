import pytest
import asyncio
from app.db.models import QuestionModel, QuestionType, CandidateAnswerModel, ScoreBreakdown
from app.services.scoring_service import ScoringService
from app.services.gemini_service import GeminiService

def test_evaluate_technical_answer():
    question = QuestionModel(
        id="JAVA_001",
        skill="Java",
        difficulty="medium",
        type=QuestionType.TECHNICAL,
        question="What is final, finally, and finalize?",
        expected_concepts=["final keyword", "finally block", "finalize method"],
        ideal_answer="final is constant, finally executes always, finalize is for GC."
    )
    
    transcript = "The final keyword makes variables constant. The finally block executes after try catch. The finalize method is called by garbage collector."
    metrics = {"wpm": 130.0, "filler_count": 1}
    
    res = ScoringService.evaluate_single_answer(question, transcript, metrics)
    assert res["technical_score"] >= 75.0
    assert res["quality_score"] >= 70.0

def test_evaluate_pseudocode_answer():
    question = QuestionModel(
        id="PSEUDO_001",
        skill="Java",
        difficulty="medium",
        type=QuestionType.PSEUDOCODE,
        question="What is output?",
        options=["4", "6", "0"],
        correct_answer="4"
    )
    
    # 1. Correct option clicked
    res_correct = ScoringService.evaluate_single_answer(question, "", {}, selected_option="4")
    assert res_correct["technical_score"] == 100.0
    assert res_correct["quality_score"] == 100.0
    
    # 2. Wrong option clicked (even if candidate spoke correct answer in mic)
    res_wrong = ScoringService.evaluate_single_answer(question, "The answer is 4", {}, selected_option="6")
    assert res_wrong["technical_score"] == 0.0
    assert res_wrong["quality_score"] == 0.0

    # 3. No option clicked (even if candidate spoke correct answer in mic)
    res_unselected = ScoringService.evaluate_single_answer(question, "The answer is 4", {}, selected_option=None)
    assert res_unselected["technical_score"] == 0.0
    assert res_unselected["quality_score"] == 0.0

def test_gemini_fallback_when_key_missing(monkeypatch):
    # Ensure GEMINI_API_KEY is empty
    from app.config import settings
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")

    skills = ["Python", "Docker"]
    scores = ScoreBreakdown(overall_score=78.0, technical_knowledge=80.0, communication=75.0)
    
    feedback = asyncio.run(
        GeminiService.generate_feedback(skills, [], [], scores)
    )
    
    assert feedback.is_fallback is True
    assert feedback.overall_summary != ""
    assert len(feedback.strengths) >= 1
    assert len(feedback.areas_to_improve) >= 1
