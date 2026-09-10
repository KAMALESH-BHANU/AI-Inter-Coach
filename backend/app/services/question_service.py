import os
import json
import random
import copy
from typing import List, Dict, Any, Tuple, Optional
from app.db.models import QuestionModel, QuestionType
from app.utils.logger import logger

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "questions")
SKILLS_DIR = os.path.join(DATA_DIR, "skills")
PROJECT_QUESTIONS_FILE = os.path.join(DATA_DIR, "project_questions.json")
PSEUDOCODE_FILE = os.path.join(DATA_DIR, "pseudocode.json")

# Comprehensive Categorized Skill Taxonomy (Easily extendable)
CATEGORIZED_SKILLS: Dict[str, List[str]] = {
    "Programming Languages": [
        "Java", "Python", "C", "C++", "JavaScript", "TypeScript", "Go", "Rust", "Ruby", "PHP", "Swift", "Kotlin", "C#"
    ],
    "Frontend": [
        "HTML", "CSS", "React", "Next.js", "Vue.js", "Angular", "Tailwind CSS", "Redux", "Svelte"
    ],
    "Backend": [
        "Node.js", "Express.js", "Spring", "Spring Boot", "Hibernate", "Django", "FastAPI", "Flask", "ASP.NET", "REST API", "Microservices", "GraphQL"
    ],
    "Databases": [
        "MySQL", "PostgreSQL", "MongoDB", "SQL", "Redis", "Oracle", "Cassandra", "SQLite"
    ],
    "Core Computer Science": [
        "Data Structures", "Algorithms", "OOP", "Operating Systems", "Computer Networks", "DBMS", "System Design"
    ],
    "DevOps and Cloud": [
        "Git", "GitHub", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "CI/CD", "Linux"
    ],
    "AI and Data Science": [
        "Machine Learning", "Deep Learning", "Artificial Intelligence", "Generative AI", "NLP", "Computer Vision",
        "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "Data Analytics", "Data Science", "Power BI", "LLMs", "LangChain"
    ]
}

# Flattened list of all taxonomy skills
TAXONOMY_SKILLS: List[str] = sorted(list({skill for sublist in CATEGORIZED_SKILLS.values() for skill in sublist}))

class QuestionService:
    @staticmethod
    def shuffle_list(items: List[Any]) -> List[Any]:
        """
        Fisher-Yates shuffle algorithm executed on an isolated copy.
        Never modifies the original array or question bank in memory.
        """
        shuffled = copy.deepcopy(items)
        n = len(shuffled)
        for i in range(n - 1, 0, -1):
            j = random.randint(0, i)
            shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
        return shuffled

    @staticmethod
    def load_skill_questions(skill: str) -> List[Dict[str, Any]]:
        """
        Loads question bank for a specific skill from JSON file.
        """
        normalized_name = skill.lower().replace(' ', '').replace('.', '').replace('/', '').replace('#', 'sharp') + ".json"
        filepath = os.path.join(SKILLS_DIR, normalized_name)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading skill question file {filepath}: {e}")

        # Fallback question set if skill file not yet seeded
        return [
            {
                "id": f"{skill.upper().replace(' ', '_').replace('.', '_')}_GEN_01",
                "skill": skill,
                "difficulty": "medium",
                "question": f"Explain the core architectural concepts, design patterns, and standard best practices when engineering production systems with {skill}.",
                "expected_concepts": [f"{skill} fundamentals", "Architecture", "Best Practices", "Error Handling"],
                "ideal_answer": f"Describes design principles, modular structure, performance considerations, and error handling with {skill}."
            },
            {
                "id": f"{skill.upper().replace(' ', '_').replace('.', '_')}_GEN_02",
                "skill": skill,
                "difficulty": "medium",
                "question": f"What are common performance bottlenecks and memory management considerations when working with {skill}?",
                "expected_concepts": ["Performance Optimization", "Memory Management", "Concurrency", "Profiling"],
                "ideal_answer": f"Details memory allocation, garbage collection or lifecycle management, and optimization techniques in {skill}."
            }
        ]

    @staticmethod
    def load_project_questions() -> List[Dict[str, Any]]:
        """
        Loads general project question pool.
        """
        if os.path.exists(PROJECT_QUESTIONS_FILE):
            try:
                with open(PROJECT_QUESTIONS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading project questions file {PROJECT_QUESTIONS_FILE}: {e}")
        return []

    @staticmethod
    def load_pseudocode_questions() -> List[Dict[str, Any]]:
        """
        Loads pseudocode and code-tracing question pool.
        """
        if os.path.exists(PSEUDOCODE_FILE):
            try:
                with open(PSEUDOCODE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading pseudocode file {PSEUDOCODE_FILE}: {e}")
        return []

    @classmethod
    def generate_interview_questions(
        cls, 
        candidate_skills: List[str], 
        projects: Optional[List[Dict[str, Any]]] = None,
        recent_question_ids: Optional[List[str]] = None
    ) -> List[QuestionModel]:
        """
        Strict 10-Question Random Generator:
        - Exactly 3 Project Questions
        - Exactly 5 Skill-Based Technical Questions
        - Exactly 2 Pseudocode / Output Questions
        = Exactly 10 Total Questions
        """
        recent_ids = set(recent_question_ids or [])
        if not candidate_skills:
            candidate_skills = ["Java", "Python", "Data Structures"]

        selected_questions: List[QuestionModel] = []
        used_ids = set()
        used_texts = set()

        # =========================================================================
        # 1. SELECT EXACTLY 3 PROJECT QUESTIONS
        # =========================================================================
        project_q_models: List[QuestionModel] = []

        if projects and len(projects) > 0:
            proj = projects[0]
            proj_name = proj.get("name", "your main project")
            proj_techs = ", ".join(proj.get("technologies", candidate_skills[:3]))
            
            pers_candidates = [
                QuestionModel(
                    id=f"PROJ_PERS_001_{abs(hash(proj_name)) % 10000}",
                    skill="Project Architecture",
                    difficulty="medium",
                    type=QuestionType.PROJECT,
                    question=f"Walk me through the overall architecture of your project '{proj_name}' built using {proj_techs}.",
                    expected_concepts=["Architecture", "Component Design", "Tech Selection", "Data Flow"],
                    ideal_answer=f"Detailed description of '{proj_name}' architecture, technology choices, and data flow."
                ),
                QuestionModel(
                    id=f"PROJ_PERS_002_{abs(hash(proj_name)) % 10000}",
                    skill="Project Challenge",
                    difficulty="medium",
                    type=QuestionType.PROJECT,
                    question=f"What was the most critical technical challenge or bug you faced while implementing '{proj_name}', and how did you diagnose and resolve it?",
                    expected_concepts=["Problem Diagnosis", "Debugging", "Root Cause Analysis", "Resolution"],
                    ideal_answer=f"Specific challenge in '{proj_name}', step-by-step diagnosis, and effective resolution."
                ),
                QuestionModel(
                    id=f"PROJ_PERS_003_{abs(hash(proj_name)) % 10000}",
                    skill="Project Optimization",
                    difficulty="medium",
                    type=QuestionType.PROJECT,
                    question=f"If you were to scale '{proj_name}' to support 100x user traffic, what architectural and database improvements would you make?",
                    expected_concepts=["Scalability", "Caching", "Database Indexing", "Load Balancing"],
                    ideal_answer="Design improvements, database indexing, caching strategies, or architectural updates."
                )
            ]
            for pq in pers_candidates:
                project_q_models.append(pq)
                used_ids.add(pq.id)
                used_texts.add(pq.question)
        else:
            # Random selection from project question bank using Fisher-Yates shuffle
            raw_proj_pool = cls.load_project_questions()
            shuffled_proj_pool = cls.shuffle_list(raw_proj_pool)

            # Prioritize questions not asked in recent sessions
            fresh_pool = [q for q in shuffled_proj_pool if q["id"] not in recent_ids]
            candidate_pool = fresh_pool if len(fresh_pool) >= 3 else shuffled_proj_pool

            for item in candidate_pool:
                if len(project_q_models) >= 3:
                    break
                if item["id"] not in used_ids and item["question"] not in used_texts:
                    project_q_models.append(
                        QuestionModel(
                            id=item["id"],
                            skill=item.get("skill", "Project Architecture"),
                            difficulty=item.get("difficulty", "medium"),
                            type=QuestionType.PROJECT,
                            question=item["question"],
                            expected_concepts=item.get("expected_concepts", []),
                            ideal_answer=item.get("ideal_answer", "")
                        )
                    )
                    used_ids.add(item["id"])
                    used_texts.add(item["question"])

        # Ensure exactly 3 project questions
        selected_questions.extend(project_q_models[:3])

        # =========================================================================
        # 2. SELECT EXACTLY 5 TECHNICAL QUESTIONS (Distributed across skills)
        # =========================================================================
        tech_q_models: List[QuestionModel] = []
        shuffled_skills = cls.shuffle_list(candidate_skills)

        # Distribute 5 questions across available skills dynamically
        skill_turn = 0
        max_search_passes = 10
        current_pass = 0

        while len(tech_q_models) < 5 and current_pass < max_search_passes:
            current_pass += 1
            for skill in shuffled_skills:
                if len(tech_q_models) >= 5:
                    break

                raw_skill_qs = cls.load_skill_questions(skill)
                shuffled_skill_qs = cls.shuffle_list(raw_skill_qs)

                # Prioritize unseen question IDs first
                unseen = [q for q in shuffled_skill_qs if q["id"] not in used_ids and q["id"] not in recent_ids and q["question"] not in used_texts]
                choice_item = unseen[0] if unseen else None

                if not choice_item:
                    # Fallback to any unused in this session
                    available = [q for q in shuffled_skill_qs if q["id"] not in used_ids and q["question"] not in used_texts]
                    choice_item = available[0] if available else None

                if choice_item:
                    tech_q_models.append(
                        QuestionModel(
                            id=choice_item["id"],
                            skill=choice_item.get("skill", skill),
                            difficulty=choice_item.get("difficulty", "medium"),
                            type=QuestionType.TECHNICAL,
                            question=choice_item["question"],
                            expected_concepts=choice_item.get("expected_concepts", []),
                            ideal_answer=choice_item.get("ideal_answer", ""),
                            explanation=choice_item.get("explanation")
                        )
                    )
                    used_ids.add(choice_item["id"])
                    used_texts.add(choice_item["question"])

        # Fallback generator if pool was insufficient
        while len(tech_q_models) < 5:
            fallback_num = len(tech_q_models) + 1
            fallback_skill = shuffled_skills[fallback_num % len(shuffled_skills)]
            fid = f"TECH_FALLBACK_{fallback_skill.upper().replace(' ', '_')}_{fallback_num}"
            q_text = f"Explain the core mechanisms, modular design, and robust error handling best practices when implementing {fallback_skill} in production."
            if fid not in used_ids and q_text not in used_texts:
                tech_q_models.append(
                    QuestionModel(
                        id=fid,
                        skill=fallback_skill,
                        difficulty="medium",
                        type=QuestionType.TECHNICAL,
                        question=q_text,
                        expected_concepts=[fallback_skill, "Software Design", "Error Handling"],
                        ideal_answer=f"Modular design, lifecycle management, and resilience in {fallback_skill}."
                    )
                )
                used_ids.add(fid)
                used_texts.add(q_text)

        selected_questions.extend(tech_q_models[:5])

        # =========================================================================
        # 3. SELECT EXACTLY 2 PSEUDOCODE / OUTPUT QUESTIONS
        # =========================================================================
        pseudo_q_models: List[QuestionModel] = []
        raw_pseudo_pool = cls.load_pseudocode_questions()
        shuffled_pseudo_pool = cls.shuffle_list(raw_pseudo_pool)

        # Prioritize unseen pseudocode questions
        fresh_pseudo = [q for q in shuffled_pseudo_pool if q["id"] not in recent_ids and q["id"] not in used_ids and q["question"] not in used_texts]
        pseudo_candidates = fresh_pseudo if len(fresh_pseudo) >= 2 else shuffled_pseudo_pool

        for item in pseudo_candidates:
            if len(pseudo_q_models) >= 2:
                break
            if item["id"] not in used_ids and item["question"] not in used_texts:
                pseudo_q_models.append(
                    QuestionModel(
                        id=item["id"],
                        skill=item.get("language", "Pseudocode"),
                        difficulty=item.get("difficulty", "medium"),
                        type=QuestionType.PSEUDOCODE,
                        question=item["question"],
                        options=item.get("options"),
                        correct_answer=item.get("correct_answer"),
                        explanation=item.get("explanation"),
                        expected_concepts=["Logic Analysis", "Code Tracing", "Syntax Understanding"],
                        ideal_answer=f"Correct answer: {item.get('correct_answer')}. Explanation: {item.get('explanation')}"
                    )
                )
                used_ids.add(item["id"])
                used_texts.add(item["question"])

        # Fallback if needed
        while len(pseudo_q_models) < 2:
            pid = f"PSEUDO_GEN_{len(pseudo_q_models) + 1}"
            pseudo_q_models.append(
                QuestionModel(
                    id=pid,
                    skill="Algorithms",
                    difficulty="easy",
                    type=QuestionType.PSEUDOCODE,
                    question="What is the average time complexity of searching for an element in a Hash Table with optimal hashing?",
                    options=["O(1)", "O(log n)", "O(n)", "O(n log n)"],
                    correct_answer="O(1)",
                    explanation="Hash tables provide direct index computation using the key's hash value, achieving O(1) average lookup time.",
                    expected_concepts=["Hash Table", "Time Complexity", "Constant Time"],
                    ideal_answer="Correct answer: O(1)"
                )
            )
            used_ids.add(pid)

        selected_questions.extend(pseudo_q_models[:2])

        # =========================================================================
        # 4. FINAL VALIDATION (Enforce strict 3 + 5 + 2 = 10 Question Set)
        # =========================================================================
        is_valid, validation_msg = cls.validate_question_set(selected_questions, candidate_skills)
        if not is_valid:
            logger.error(f"Critical question validation failure: {validation_msg}")
            raise ValueError(f"Invalid question set generated: {validation_msg}")

        return selected_questions

    @staticmethod
    def validate_question_set(questions: List[QuestionModel], candidate_skills: List[str]) -> Tuple[bool, str]:
        """
        Validates the strict 3 + 5 + 2 = 10 question distribution contract:
        - Exactly 10 total questions
        - Exactly 3 project questions
        - Exactly 5 technical questions
        - Exactly 2 pseudocode questions
        - 100% unique question IDs
        - 100% unique question texts
        """
        if len(questions) != 10:
            return False, f"Expected exactly 10 questions, got {len(questions)}"

        project_qs = [q for q in questions if q.type == QuestionType.PROJECT]
        tech_qs = [q for q in questions if q.type == QuestionType.TECHNICAL]
        pseudo_qs = [q for q in questions if q.type == QuestionType.PSEUDOCODE]

        if len(project_qs) != 3:
            return False, f"Expected exactly 3 project questions, got {len(project_qs)}"
        if len(tech_qs) != 5:
            return False, f"Expected exactly 5 technical skill questions, got {len(tech_qs)}"
        if len(pseudo_qs) != 2:
            return False, f"Expected exactly 2 pseudocode questions, got {len(pseudo_qs)}"

        q_ids = [q.id for q in questions]
        if len(set(q_ids)) != 10:
            return False, f"Duplicate question IDs detected: {q_ids}"

        q_texts = [q.question.strip() for q in questions]
        if len(set(q_texts)) != 10:
            return False, "Duplicate question texts detected in session"

        return True, "Valid"
