import pytest
from app.db.models import QuestionModel, QuestionType
from app.services.question_service import QuestionService, TAXONOMY_SKILLS, CATEGORIZED_SKILLS

def test_generate_interview_questions_validity():
    skills = ["Java", "Python", "React", "MySQL"]
    questions = QuestionService.generate_interview_questions(skills)
    
    is_valid, msg = QuestionService.validate_question_set(questions, skills)
    assert is_valid, f"Validation failed: {msg}"
    assert len(questions) == 10

def test_question_counts_distribution():
    skills = ["Java", "Spring Boot", "MySQL", "React"]
    questions = QuestionService.generate_interview_questions(skills)
    
    project_qs = [q for q in questions if q.type == QuestionType.PROJECT]
    tech_qs = [q for q in questions if q.type == QuestionType.TECHNICAL]
    pseudo_qs = [q for q in questions if q.type == QuestionType.PSEUDOCODE]
    
    assert len(project_qs) == 3, f"Expected 3 project questions, got {len(project_qs)}"
    assert len(tech_qs) == 5, f"Expected 5 technical questions, got {len(tech_qs)}"
    assert len(pseudo_qs) == 2, f"Expected 2 pseudocode questions, got {len(pseudo_qs)}"
    assert len(questions) == 10

def test_no_duplicate_ids_or_texts():
    skills = ["Python", "Docker", "AWS", "FastAPI"]
    questions = QuestionService.generate_interview_questions(skills)
    ids = [q.id for q in questions]
    texts = [q.question.strip() for q in questions]
    
    assert len(set(ids)) == 10, "Duplicate question IDs found"
    assert len(set(texts)) == 10, "Duplicate question texts found"

def test_randomization_across_interviews():
    skills = ["Java", "Python", "React", "MySQL"]
    
    # Run two independent generation calls
    set_1 = QuestionService.generate_interview_questions(skills)
    ids_1 = [q.id for q in set_1]
    
    # Second interview with recent IDs passed
    set_2 = QuestionService.generate_interview_questions(skills, recent_question_ids=ids_1)
    ids_2 = [q.id for q in set_2]
    
    assert len(set_1) == 10
    assert len(set_2) == 10
    # Overlap should be minimized or question order varied
    assert ids_1 != ids_2, "Two consecutive interviews generated identical question order/IDs"

def test_categorized_skills_taxonomy():
    assert len(CATEGORIZED_SKILLS) >= 7
    assert "Programming Languages" in CATEGORIZED_SKILLS
    assert "Frontend" in CATEGORIZED_SKILLS
    assert "Backend" in CATEGORIZED_SKILLS
    assert "Databases" in CATEGORIZED_SKILLS
    assert "Core Computer Science" in CATEGORIZED_SKILLS
    assert "DevOps and Cloud" in CATEGORIZED_SKILLS
    assert "AI and Data Science" in CATEGORIZED_SKILLS
    assert len(TAXONOMY_SKILLS) >= 45

def test_invalid_counts_rejection():
    invalid_questions = [
        QuestionModel(id=f"P_{i}", skill="Project", difficulty="medium", type=QuestionType.PROJECT, question=f"Q {i}?")
        for i in range(4)
    ] + [
        QuestionModel(id=f"T_{i}", skill="Java", difficulty="medium", type=QuestionType.TECHNICAL, question=f"QT {i}?")
        for i in range(4)
    ] + [
        QuestionModel(id=f"PS_{i}", skill="Pseudocode", difficulty="medium", type=QuestionType.PSEUDOCODE, question=f"QPS {i}?")
        for i in range(2)
    ]
    
    is_valid, msg = QuestionService.validate_question_set(invalid_questions, ["Java"])
    assert not is_valid
    assert "Expected exactly 3 project questions" in msg

def test_duplicate_id_rejection():
    invalid_questions = [
        QuestionModel(id="DUP_1", skill="Project", difficulty="medium", type=QuestionType.PROJECT, question=f"Q {i}?")
        for i in range(3)
    ] + [
        QuestionModel(id=f"T_{i}", skill="Java", difficulty="medium", type=QuestionType.TECHNICAL, question=f"QT {i}?")
        for i in range(5)
    ] + [
        QuestionModel(id=f"PS_{i}", skill="Pseudocode", difficulty="medium", type=QuestionType.PSEUDOCODE, question=f"QPS {i}?")
        for i in range(2)
    ]
    
    is_valid, msg = QuestionService.validate_question_set(invalid_questions, ["Java"])
    assert not is_valid
    assert "Duplicate question IDs" in msg
