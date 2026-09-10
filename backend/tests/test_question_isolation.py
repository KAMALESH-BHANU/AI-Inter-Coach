import pytest
from app.db.models import CandidateAnswerModel, QuestionModel, QuestionType

def test_question_answer_isolation():
    q1 = QuestionModel(
        id="Q1",
        skill="Java",
        difficulty="medium",
        type=QuestionType.TECHNICAL,
        question="What is OOP?"
    )
    q2 = QuestionModel(
        id="Q2",
        skill="React",
        difficulty="medium",
        type=QuestionType.TECHNICAL,
        question="What is JSX?"
    )

    ans1 = CandidateAnswerModel(
        question_id="Q1",
        question_index=0,
        transcript="Java is object oriented",
        wpm=130.0,
        filler_count=1
    )

    ans2 = CandidateAnswerModel(
        question_id="Q2",
        question_index=1,
        transcript="JSX is JavaScript XML",
        wpm=140.0,
        filler_count=0
    )

    assert ans1.transcript != ans2.transcript
    assert "Java is object oriented" not in ans2.transcript
    assert ans1.question_id == "Q1"
    assert ans2.question_id == "Q2"
