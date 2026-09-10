import pytest
from app.db.models import InterviewSessionModel, QuestionModel, QuestionType, CandidateAnswerModel, ScoreBreakdown
from app.services.report_service import ReportService

def test_pdf_report_generation():
    questions = [
        QuestionModel(id=f"Q_{i}", skill="Java", difficulty="medium", type=QuestionType.TECHNICAL, question="Sample Q?")
        for i in range(10)
    ]
    answers = [
        CandidateAnswerModel(question_id=f"Q_{i}", question_index=i, transcript="Sample answer transcript text", technical_score=85.0)
        for i in range(10)
    ]
    scores = ScoreBreakdown(overall_score=85.0, technical_knowledge=85.0, communication=80.0, eye_contact=82.0)
    
    session = InterviewSessionModel(
        id="test-session-12345",
        user_id="user-1",
        skills=["Java", "Spring Boot"],
        questions=questions,
        answers=answers,
        scores=scores
    )

    pdf_bytes = ReportService.generate_pdf_report(session, "Kamalesh Banu")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
