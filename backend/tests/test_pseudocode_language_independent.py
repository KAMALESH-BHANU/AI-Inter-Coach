import pytest
import os
import json
import re
from app.db.models import QuestionModel, QuestionType, CandidateAnswerModel
from app.services.question_service import QuestionService
from app.services.scoring_service import ScoringService

def test_pseudocode_four_options_and_attributes():
    """Test 1 & Test 2: Exactly 4 options and valid correct answer per question"""
    bank = QuestionService.load_pseudocode_questions()
    assert len(bank) >= 50, f"Expected at least 50 pseudocode questions, found {len(bank)}"
    
    categories = set()
    for item in bank:
        assert item.get("languageIndependent") is True or item.get("language_independent") is True
        assert item.get("options") is not None
        assert len(item["options"]) == 4, f"Question {item['id']} must have exactly 4 options"
        
        opt_ids = [opt["id"] for opt in item["options"]]
        assert opt_ids == ["A", "B", "C", "D"], f"Question {item['id']} option IDs must be A, B, C, D"
        
        corr = item.get("correctOptionId") or item.get("correct_option_id") or item.get("correct_answer")
        assert corr in ["A", "B", "C", "D"], f"Question {item['id']} has invalid correct option {corr}"
        
        assert item.get("pseudocode") or item.get("code_snippet"), f"Question {item['id']} missing pseudocode"
        assert item.get("input") or item.get("input_description"), f"Question {item['id']} missing input"
        
        categories.add(item.get("category"))
        
        # Test model conversion & validation
        is_valid = QuestionService.validate_pseudocode_question(item)
        assert is_valid, f"Validation failed for {item['id']}"

    assert "CONDITIONS" in categories
    assert "LOOPS" in categories
    assert "ARRAYS" in categories
    assert "SEARCHING" in categories
    assert "SORTING" in categories
    assert "STRINGS" in categories
    assert "BASIC_ALGORITHMS" in categories

def test_no_programming_language_specific_syntax():
    """Verify strictly generic pseudocode without language keywords"""
    bank = QuestionService.load_pseudocode_questions()
    
    forbidden_patterns = [
        r"\bSystem\.out\b", r"\bconsole\.log\b", r"\bprint\s*\(", r"\bprintf\s*\(",
        r"\bcout\s*<<", r"\bcin\s*>>", r"\bpublic\s+class\b", r"\bpublic\s+static\b",
        r"\bdef\s+[a-zA-Z_]", r"\b#include\b", r"\bimport\s+[a-zA-Z_]",
        r"\bfrom\s+[a-zA-Z_]+\s+import\b", r"\bstd::", r"\bint\s+main\b",
        r"\bchar\*", r"\bNone\b", r"\bnullptr\b",
        r"\bList<", r"\bArrayList<", r"\bvector<", r"\bHashMap<", r"\bMap<",
        r"\bdict\(", r"\bset\(", r"\blet\s+", r"\bvar\s+",
        r"\bconst\s+", r"\bfn\b", r"\bfunc\b"
    ]
    
    for item in bank:
        content_to_check = f"{item.get('question','')} {item.get('pseudocode', '')} {item.get('code_snippet', '')} {item.get('input', '')} {item.get('input_description', '')}"
        for pattern in forbidden_patterns:
            match = re.search(pattern, content_to_check, re.IGNORECASE)
            assert match is None, f"Forbidden language pattern '{pattern}' matched in {item['id']}: {match.group(0)}"

def test_skills_do_not_alter_pseudocode_language_independence():
    """Test 10: Technical questions depend on skills, but pseudocode MCQs remain language-independent"""
    skill_sets = [
        ["Java", "Spring Boot", "MySQL", "Hibernate"],
        ["Python", "Django", "FastAPI", "PostgreSQL"],
        ["C++", "Data Structures", "Algorithms", "Qt"],
        ["JavaScript", "React", "Node.js", "Express.js"],
        ["Go", "Kubernetes", "Docker", "AWS"],
    ]
    
    for skills in skill_sets:
        questions = QuestionService.generate_interview_questions(skills)
        assert len(questions) == 13
        
        pseudo_qs = [q for q in questions if q.type in [QuestionType.PSEUDOCODE, QuestionType.PSEUDOCODE_MCQ]]
        assert len(pseudo_qs) == 2, f"Expected 2 pseudocode questions for skills {skills}, got {len(pseudo_qs)}"
        
        for q in pseudo_qs:
            assert q.language_independent is True
            assert q.supported_languages == ["language-independent"]
            assert q.skill not in ["Java", "Python", "C++", "JavaScript", "Go"]
            assert q.options is not None and len(q.options) == 4
            assert q.correct_option_id in ["A", "B", "C", "D"]
            
            is_valid = QuestionService.validate_pseudocode_question(q)
            assert is_valid, f"Validation failed for {q.id}"

def test_pseudocode_random_distinct_selection():
    """Test 3 & Test 4: Random selection of 2 distinct pseudocode questions"""
    pseudo_qs = QuestionService.get_dynamic_pseudocode_questions(count=2)
    assert len(pseudo_qs) == 2
    assert pseudo_qs[0].id != pseudo_qs[1].id
    
    # Avoid recent IDs
    recent = [pseudo_qs[0].id, pseudo_qs[1].id]
    pseudo_qs_next = QuestionService.get_dynamic_pseudocode_questions(count=2, recent_ids=recent)
    assert len(pseudo_qs_next) == 2
    assert pseudo_qs_next[0].id not in recent
    assert pseudo_qs_next[1].id not in recent

def test_pseudocode_scoring_correct_option():
    """Test 6: Correct option gives 1/1 (100% score)"""
    pseudo_qs = QuestionService.get_dynamic_pseudocode_questions(count=1)
    sample_q = pseudo_qs[0]
    corr_id = sample_q.correct_option_id or sample_q.correctOptionId
    
    eval_result = ScoringService.evaluate_single_answer(
        question=sample_q,
        selected_option=corr_id
    )
    
    assert eval_result["technical_score"] == 100.0
    assert eval_result["is_correct"] is True

def test_pseudocode_scoring_incorrect_option():
    """Test 7: Incorrect option gives 0/1 (0% score)"""
    pseudo_qs = QuestionService.get_dynamic_pseudocode_questions(count=1)
    sample_q = pseudo_qs[0]
    corr_id = sample_q.correct_option_id or sample_q.correctOptionId
    wrong_id = "A" if corr_id != "A" else "B"
    
    eval_result = ScoringService.evaluate_single_answer(
        question=sample_q,
        selected_option=wrong_id
    )
    
    assert eval_result["technical_score"] == 0.0
    assert eval_result["is_correct"] is False

def test_pseudocode_scoring_unanswered():
    """Test 8: Unanswered question gives 0/1 and 0 score"""
    pseudo_qs = QuestionService.get_dynamic_pseudocode_questions(count=1)
    sample_q = pseudo_qs[0]
    
    eval_result = ScoringService.evaluate_single_answer(
        question=sample_q,
        selected_option=None
    )
    
    assert eval_result["technical_score"] == 0.0
    assert eval_result["is_correct"] is False

def test_score_integrity_backend_calculation():
    """Test 11: Backend calculates score ignoring fake scores in payload"""
    pseudo_qs = QuestionService.get_dynamic_pseudocode_questions(count=1)
    sample_q = pseudo_qs[0]
    corr_id = sample_q.correct_option_id or sample_q.correctOptionId
    wrong_id = "A" if corr_id != "A" else "B"
    
    # Attempting to pass a fake score with wrong answer
    eval_result = ScoringService.evaluate_single_answer(
        question=sample_q,
        selected_option=wrong_id,
        metrics={"fake_score": 100.0, "technical_score": 100.0}
    )
    
    assert eval_result["technical_score"] == 0.0
    assert eval_result["is_correct"] is False

def test_pseudocode_session_score_aggregation():
    """Test session aggregation for 0/2, 1/2, 2/2 pseudocode scores"""
    pseudo_qs = QuestionService.get_dynamic_pseudocode_questions(count=2)
    q1, q2 = pseudo_qs[0], pseudo_qs[1]
    
    # Case 1: 2 correct -> 100%
    ans1 = CandidateAnswerModel(
        question_id=q1.id, question_index=9, selected_option=q1.correct_option_id,
        technical_score=100.0, quality_score=100.0, communication_score=100.0, is_correct=True
    )
    ans2 = CandidateAnswerModel(
        question_id=q2.id, question_index=10, selected_option=q2.correct_option_id,
        technical_score=100.0, quality_score=100.0, communication_score=100.0, is_correct=True
    )
    scores = ScoringService.aggregate_session_scores([q1, q2], [ans1, ans2])
    assert scores.pseudocode_score == 100.0
    
    # Case 2: 1 correct -> 50%
    ans2_wrong = CandidateAnswerModel(
        question_id=q2.id, question_index=10, selected_option="Z",
        technical_score=0.0, quality_score=0.0, communication_score=0.0, is_correct=False
    )
    scores_half = ScoringService.aggregate_session_scores([q1, q2], [ans1, ans2_wrong])
    assert scores_half.pseudocode_score == 50.0

def test_interview_13_question_structure_with_mcq():
    """Test 12: Verify full 13-question sequence contract"""
    skills = ["Java", "Spring Boot", "MySQL", "React"]
    questions = QuestionService.generate_interview_questions(skills)
    
    assert len(questions) == 13
    assert questions[0].type == QuestionType.INTRODUCTION
    assert questions[1].type == QuestionType.PROJECT
    assert questions[2].type == QuestionType.PROJECT
    assert questions[3].type == QuestionType.PROJECT
    for i in range(4, 9):
        assert questions[i].type == QuestionType.TECHNICAL
    assert questions[9].type in [QuestionType.PSEUDOCODE, QuestionType.PSEUDOCODE_MCQ]
    assert questions[10].type in [QuestionType.PSEUDOCODE, QuestionType.PSEUDOCODE_MCQ]
    assert questions[11].type == QuestionType.SQL
    assert questions[12].type == QuestionType.SQL
    
    is_valid, msg = QuestionService.validate_question_set(questions, skills)
    assert is_valid, f"13-question validation failed: {msg}"
