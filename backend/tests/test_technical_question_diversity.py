import os
import pytest
from app.services.question_service import (
    QuestionService,
    CATEGORIZED_SKILLS,
    TAXONOMY_SKILLS,
    normalize_question_text,
    create_question_fingerprint
)
from app.db.models import QuestionType, QuestionModel

def test_all_74_skills_in_taxonomy_and_banks():
    """Test 1: Every skill in the 74-skill taxonomy has at least 15 valid questions."""
    is_valid, errors = QuestionService.validate_technical_question_bank()
    assert is_valid, f"Question bank validation failed with errors: {errors}"
    assert len(errors) == 0

def test_unique_question_ids_across_all_banks():
    """Test 2: All 1,110+ question IDs across all 74 skill files are globally unique."""
    seen_ids = set()
    total_count = 0
    for cat, skills in CATEGORIZED_SKILLS.items():
        for skill in skills:
            questions = QuestionService.load_skill_questions(skill)
            assert len(questions) >= 15, f"Skill '{skill}' has fewer than 15 questions ({len(questions)})"
            for q in questions:
                total_count += 1
                qid = q.get("id")
                assert qid, f"Skill '{skill}' question missing ID"
                assert qid not in seen_ids, f"Duplicate question ID '{qid}' found in skill '{skill}'"
                seen_ids.add(qid)
    
    assert total_count >= 74 * 15
    assert len(seen_ids) == total_count

def test_exact_duplicate_rejection():
    """Test 3: Normalized exact duplicate questions are properly identified and rejected."""
    q_orig = "How does the JVM garbage collector work in Java?"
    q_copy = "  how does the jvm garbage collector work in java?  "
    
    assert normalize_question_text(q_orig) == normalize_question_text(q_copy)

    mock_pool = [
        {"id": "JAVA_001", "skill": "Java", "question": q_orig, "topic": "JVM Internals", "concept": "GC", "questionFamily": "Memory", "tags": ["Java"]},
        {"id": "JAVA_002", "skill": "Java", "question": q_copy, "topic": "JVM Internals", "concept": "GC", "questionFamily": "Memory", "tags": ["Java"]}
    ]
    used_ids = set()
    used_fps = set()
    used_texts = set()
    chosen = QuestionService.select_diverse_questions(
        questions_pool=mock_pool,
        count=2,
        used_ids=used_ids,
        used_fingerprints=used_fps,
        used_texts=used_texts
    )
    # Exactly one question is selected, the duplicate is rejected
    assert len(chosen) == 1
    assert chosen[0].id in ["JAVA_001", "JAVA_002"]

def test_skill_name_replacement_duplicate_detection():
    """Test 4: Questions that differ only by skill name produce identical fingerprints."""
    q_ai = "Explain a major technical challenge or common pitfall when using Artificial Intelligence in production and how to avoid it."
    q_cpp = "Explain a major technical challenge or common pitfall when using C++ in production and how to avoid it."

    fp_ai = create_question_fingerprint(q_ai)
    fp_cpp = create_question_fingerprint(q_cpp)

    assert fp_ai == fp_cpp, f"Fingerprints should match for template clones: '{fp_ai}' vs '{fp_cpp}'"

    mock_pool = [
        {"id": "AI_001", "skill": "Artificial Intelligence", "question": q_ai, "topic": "Challenges", "concept": "Production", "questionFamily": "Best Practices", "tags": ["AI"]},
        {"id": "CPP_001", "skill": "C++", "question": q_cpp, "topic": "Challenges", "concept": "Production", "questionFamily": "Best Practices", "tags": ["C++"]}
    ]
    used_ids = set()
    used_fps = set()
    used_texts = set()
    chosen = QuestionService.select_diverse_questions(
        questions_pool=mock_pool,
        count=2,
        used_ids=used_ids,
        used_fingerprints=used_fps,
        used_texts=used_texts
    )
    assert len(chosen) == 1

def test_different_concepts_same_skill_accepted():
    """Test 5: Distinct questions for the same skill produce distinct fingerprints and are both accepted."""
    q_gc = "Explain the generational garbage collection strategy in Java and how G1 collector manages pause times."
    q_threads = "What is the difference between synchronized blocks, ReentrantLock, and ReadWriteLock in Java concurrency?"

    fp_gc = create_question_fingerprint(q_gc)
    fp_threads = create_question_fingerprint(q_threads)

    assert fp_gc != fp_threads

    mock_pool = [
        {"id": "JAVA_001", "skill": "Java", "question": q_gc, "topic": "JVM Internals", "concept": "Garbage Collection", "questionFamily": "Memory and Runtime Architecture", "tags": ["Java"]},
        {"id": "JAVA_002", "skill": "Java", "question": q_threads, "topic": "Concurrency", "concept": "Synchronization", "questionFamily": "Concurrency and Multithreading", "tags": ["Java"]}
    ]
    used_ids = set()
    used_fps = set()
    used_texts = set()
    chosen = QuestionService.select_diverse_questions(
        questions_pool=mock_pool,
        count=2,
        used_ids=used_ids,
        used_fingerprints=used_fps,
        used_texts=used_texts
    )
    assert len(chosen) == 2

def test_single_interview_technical_diversity():
    """Test 6: In a single interview session, technical questions (Q5-Q9) enforce topic and family diversity."""
    qs = QuestionService.generate_interview_questions(["Java"])
    tech_qs = [q for q in qs if q.type == QuestionType.TECHNICAL]
    assert len(tech_qs) == 5

    # Check topic limit (max 2 per topic)
    topic_counts = {}
    for q in tech_qs:
        top = q.topic or "General"
        topic_counts[top] = topic_counts.get(top, 0) + 1
        assert topic_counts[top] <= 2, f"Topic '{top}' exceeded max 2 questions in session ({topic_counts[top]})"

    # Check distinct families
    families = {q.question_family or q.questionFamily for q in tech_qs if q.question_family or q.questionFamily}
    assert len(families) >= 3, f"Expected at least 3 distinct question families, got {len(families)}"

    # Check distinct IDs and fingerprints
    ids = [q.id for q in tech_qs]
    fps = [create_question_fingerprint(q) for q in tech_qs]
    assert len(set(ids)) == 5
    assert len(set(fps)) == 5

def test_cross_interview_variation():
    """Test 7: Across 3 sequential interviews for a single skill, candidate receives all 15 questions without repetition."""
    recent_ids = []
    recent_fps = []
    all_interview_tech_ids = []

    for session_idx in range(3):
        qs = QuestionService.generate_interview_questions(
            candidate_skills=["Python"],
            recent_question_ids=recent_ids,
            recent_question_fingerprints=recent_fps
        )
        tech_qs = [q for q in qs if q.type == QuestionType.TECHNICAL]
        assert len(tech_qs) == 5

        session_ids = [q.id for q in tech_qs]
        session_fps = [create_question_fingerprint(q) for q in tech_qs]

        # Ensure no overlap with prior session IDs
        overlap = set(session_ids).intersection(set(recent_ids))
        assert len(overlap) == 0, f"Session {session_idx+1} repeated question IDs: {overlap}"

        all_interview_tech_ids.extend(session_ids)
        recent_ids.extend(session_ids)
        recent_fps.extend(session_fps)

    # 3 sessions of 5 questions each = 15 distinct questions
    assert len(set(all_interview_tech_ids)) == 15

def test_multiple_skills_balanced_slot_distribution():
    """Test 8: Slot distribution fairly balances 5 technical slots across candidate skills."""
    # 1 skill -> 5
    dist1 = QuestionService.distribute_question_slots(["Java"])
    assert dist1 == {"Java": 5}

    # 2 skills -> 3, 2
    dist2 = QuestionService.distribute_question_slots(["Java", "Python"])
    assert sum(dist2.values()) == 5
    assert dist2["Java"] == 3 and dist2["Python"] == 2

    # 3 skills -> 2, 2, 1
    dist3 = QuestionService.distribute_question_slots(["Java", "Python", "MySQL"])
    assert sum(dist3.values()) == 5
    assert dist3["Java"] == 2 and dist3["Python"] == 2 and dist3["MySQL"] == 1

    # 4 skills -> 2, 1, 1, 1
    dist4 = QuestionService.distribute_question_slots(["Java", "Python", "React", "Docker"])
    assert sum(dist4.values()) == 5
    assert dist4["Java"] == 2 and dist4["Python"] == 1 and dist4["React"] == 1 and dist4["Docker"] == 1

    # 5 skills -> 1, 1, 1, 1, 1
    dist5 = QuestionService.distribute_question_slots(["Java", "Python", "React", "Docker", "AWS"])
    assert sum(dist5.values()) == 5
    assert all(v == 1 for v in dist5.values())

    # Generate full interview with 3 skills
    qs = QuestionService.generate_interview_questions(["Java", "Python", "MySQL"])
    tech_qs = [q for q in qs if q.type == QuestionType.TECHNICAL]
    assert len(tech_qs) == 5
    skills_present = [q.skill for q in tech_qs]
    assert skills_present.count("Java") == 2
    assert skills_present.count("Python") == 2
    assert skills_present.count("MySQL") == 1

def test_complete_13_question_structure():
    """Test 9: Full 13-question contract validation."""
    qs = QuestionService.generate_interview_questions(
        candidate_skills=["TypeScript", "React", "Node.js"],
        projects=[{
            "name": "E-Commerce Microservices",
            "technologies": ["TypeScript", "React", "Node.js", "MongoDB"]
        }]
    )

    assert len(qs) == 13
    assert qs[0].type == QuestionType.INTRODUCTION
    assert qs[0].question == "Tell me about yourself."

    assert all(q.type == QuestionType.PROJECT for q in qs[1:4])
    assert all(q.type == QuestionType.TECHNICAL for q in qs[4:9])
    assert all(q.type in [QuestionType.PSEUDOCODE, QuestionType.PSEUDOCODE_MCQ] for q in qs[9:11])
    assert all(q.type == QuestionType.SQL for q in qs[11:13])

    for sq in qs[11:13]:
        assert len(sq.tables) == 2
        for tbl in sq.tables:
            assert len(tbl["columns"]) >= 5
            assert len(tbl["rows"]) >= 5
