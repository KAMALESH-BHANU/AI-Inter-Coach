import os
import re
import json
import random
import copy
from typing import List, Dict, Any, Tuple, Optional
from app.db.models import QuestionModel, QuestionType
from app.services.sql_service import SqlService
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

# Alias and filename mapping for robust lookup
SKILL_FILENAME_MAP: Dict[str, str] = {
    "c++": "c++.json",
    "cpp": "c++.json",
    "c#": "csharp.json",
    "csharp": "csharp.json",
    "node.js": "nodejs.json",
    "nodejs": "nodejs.json",
    "scikit-learn": "scikit-learn.json",
    "sklearn": "scikit-learn.json",
    "ci/cd": "cicd.json",
    "cicd": "cicd.json",
    "tailwind css": "tailwindcss.json",
    "tailwindcss": "tailwindcss.json",
    "tailwind": "tailwindcss.json",
    "artificial intelligence": "artificialintelligence.json",
    "ai": "artificialintelligence.json",
    "generative ai": "generativeai.json",
    "genai": "generativeai.json",
    "gen ai": "generativeai.json",
    "machine learning": "machinelearning.json",
    "ml": "machinelearning.json",
    "deep learning": "deeplearning.json",
    "dl": "deeplearning.json",
    "javascript": "javascript.json",
    "js": "javascript.json",
    "typescript": "typescript.json",
    "ts": "typescript.json",
    "react": "react.json",
    "react.js": "react.json",
    "reactjs": "react.json",
    "vue": "vuejs.json",
    "vue.js": "vuejs.json",
    "vuejs": "vuejs.json",
    "next.js": "nextjs.json",
    "nextjs": "nextjs.json",
    "express": "expressjs.json",
    "express.js": "expressjs.json",
    "expressjs": "expressjs.json",
    "spring": "spring.json",
    "spring boot": "springboot.json",
    "springboot": "springboot.json",
    "rest api": "restapi.json",
    "rest": "restapi.json",
    "restful api": "restapi.json",
    "data structures": "datastructures.json",
    "dsa": "datastructures.json",
    "computer networks": "computernetworks.json",
    "networking": "computernetworks.json",
    "operating systems": "operatingsystems.json",
    "os": "operatingsystems.json",
    "system design": "systemdesign.json",
    "power bi": "powerbi.json",
    "powerbi": "powerbi.json",
    "data analytics": "dataanalytics.json",
    "data science": "datascience.json",
    "computer vision": "computervision.json",
}

# Sorted skill terms for regex mask replacement (longest terms first)
ALL_SKILL_TERMS: List[str] = sorted(
    list(set(
        TAXONOMY_SKILLS + 
        list(SKILL_FILENAME_MAP.keys()) + 
        ["artificial intelligence", "generative ai", "machine learning", "deep learning",
         "computer networks", "operating systems", "data structures", "system design",
         "data analytics", "data science", "computer vision", "spring boot", "tailwind css",
         "scikit-learn", "express.js", "next.js", "vue.js", "node.js", "power bi", "rest api"]
    )),
    key=lambda s: len(s),
    reverse=True
)

def normalize_question_text(text: str) -> str:
    """
    Normalizes question text by lowercasing, stripping punctuation,
    and collapsing whitespace for exact duplicate comparison.
    """
    if not text:
        return ""
    t = text.lower()
    t = re.sub(r"[^a-z0-9]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def create_question_fingerprint(question: Any) -> str:
    """
    Creates a template fingerprint by replacing all skill name references with
    a generic placeholder and normalizing text. This detects questions that are
    identical template copies differing only by skill name.
    """
    if isinstance(question, QuestionModel):
        text = question.question
    elif isinstance(question, dict):
        text = question.get("question", "")
    else:
        text = str(question)

    replaced = text
    for term in ALL_SKILL_TERMS:
        escaped = re.escape(term)
        pattern = rf"(?<![a-zA-Z0-9]){escaped}(?![a-zA-Z0-9])"
        replaced = re.sub(pattern, "SKILL_PLACEHOLDER", replaced, flags=re.IGNORECASE)

    return normalize_question_text(replaced)

class QuestionService:
    normalize_question_text = staticmethod(normalize_question_text)
    create_question_fingerprint = staticmethod(create_question_fingerprint)

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
        Uses alias resolution and falls back to normalized filename lookup.
        """
        s_lower = skill.strip().lower()
        filename = SKILL_FILENAME_MAP.get(s_lower)
        if not filename:
            filename = s_lower.replace(' ', '').replace('.', '').replace('/', '').replace('#', 'sharp') + ".json"

        filepath = os.path.join(SKILLS_DIR, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading skill question file {filepath}: {e}")

        # Fallback question set if skill file not found
        return [
            {
                "id": f"{skill.upper().replace(' ', '_').replace('.', '_')}_GEN_01",
                "skill": skill,
                "difficulty": "medium",
                "topic": f"{skill} Architecture",
                "concept": "System Architecture",
                "questionFamily": "Architecture & System Design",
                "question": f"Explain the core architectural concepts, design patterns, and standard best practices when engineering production systems with {skill}.",
                "expected_concepts": [f"{skill} fundamentals", "Architecture", "Best Practices", "Error Handling"],
                "idealAnswer": f"Describes design principles, modular structure, performance considerations, and error handling with {skill}.",
                "tags": [skill, "Architecture", "Best Practices"]
            },
            {
                "id": f"{skill.upper().replace(' ', '_').replace('.', '_')}_GEN_02",
                "skill": skill,
                "difficulty": "medium",
                "topic": f"{skill} Performance",
                "concept": "Performance Tuning",
                "questionFamily": "Performance & Optimization",
                "question": f"What are common performance bottlenecks and memory management considerations when working with {skill}?",
                "expected_concepts": ["Performance Optimization", "Memory Management", "Concurrency", "Profiling"],
                "idealAnswer": f"Details memory allocation, garbage collection or lifecycle management, and optimization techniques in {skill}.",
                "tags": [skill, "Performance", "Optimization"]
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

    @staticmethod
    def distribute_question_slots(selected_skills: List[str], total_count: int = 5) -> Dict[str, int]:
        """
        Fairly distributes technical question slots across candidate skills.
        Example for 5 slots:
        - 1 skill:  [5]
        - 2 skills: [3, 2]
        - 3 skills: [2, 2, 1]
        - 4 skills: [2, 1, 1, 1]
        - 5 skills: [1, 1, 1, 1, 1]
        """
        if not selected_skills:
            return {"Java": 2, "Python": 2, "Data Structures": 1}

        unique_skills = []
        for s in selected_skills:
            if s and s not in unique_skills:
                unique_skills.append(s)

        num_skills = len(unique_skills)
        if num_skills == 0:
            return {"Java": 2, "Python": 2, "Data Structures": 1}

        slots: Dict[str, int] = {}
        if num_skills >= total_count:
            for i in range(total_count):
                slots[unique_skills[i]] = 1
            return slots

        base = total_count // num_skills
        remainder = total_count % num_skills

        for i, skill in enumerate(unique_skills):
            slots[skill] = base + (1 if i < remainder else 0)

        return slots

    @classmethod
    def select_diverse_questions(
        cls,
        questions_pool: List[Dict[str, Any]],
        count: int,
        used_ids: set,
        used_fingerprints: set,
        used_texts: set,
        recent_ids: Optional[set] = None,
        recent_fingerprints: Optional[set] = None,
        topic_counts: Optional[Dict[str, int]] = None,
        used_families: Optional[set] = None,
        used_concepts: Optional[set] = None
    ) -> List[QuestionModel]:
        """
        Selects questions ensuring:
        - No exact duplicate IDs or normalized texts
        - No semantic template copies (via fingerprints)
        - Diversity across topics (max 2 per topic)
        - Diversity across question families and concepts
        - Avoidance of recent technical questions from prior sessions
        """
        r_ids = recent_ids or set()
        r_fps = recent_fingerprints or set()
        topics = topic_counts if topic_counts is not None else {}
        families = used_families if used_families is not None else set()
        concepts = used_concepts if used_concepts is not None else set()

        shuffled = cls.shuffle_list(questions_pool)
        chosen: List[QuestionModel] = []

        def can_accept(item: Dict[str, Any], check_recent: bool = True, max_topic: int = 2, check_family: bool = False, check_concept: bool = False) -> bool:
            qid = item.get("id", "")
            qtext = item.get("question", "")
            norm_text = normalize_question_text(qtext)
            fp = create_question_fingerprint(item)
            top = item.get("topic", "General")
            fam = item.get("questionFamily") or item.get("question_family") or ""
            con = item.get("concept") or ""

            if qid in used_ids or norm_text in used_texts or fp in used_fingerprints:
                return False
            if check_recent and (qid in r_ids or fp in r_fps):
                return False
            if topics.get(top, 0) >= max_topic:
                return False
            if check_family and fam and fam in families:
                return False
            if check_concept and con and con in concepts:
                return False
            return True

        def add_question(item: Dict[str, Any]) -> QuestionModel:
            qid = item.get("id", "")
            qtext = item.get("question", "")
            norm_text = normalize_question_text(qtext)
            fp = create_question_fingerprint(item)
            top = item.get("topic", "General")
            fam = item.get("questionFamily") or item.get("question_family") or ""
            con = item.get("concept") or ""
            ideal = item.get("idealAnswer") or item.get("ideal_answer") or ""

            used_ids.add(qid)
            used_texts.add(norm_text)
            used_fingerprints.add(fp)
            topics[top] = topics.get(top, 0) + 1
            if fam:
                families.add(fam)
            if con:
                concepts.add(con)

            model = QuestionModel(
                id=qid,
                skill=item.get("skill", "General"),
                difficulty=item.get("difficulty", "medium"),
                type=QuestionType.TECHNICAL,
                question=qtext,
                topic=top,
                concept=con,
                question_family=fam,
                questionFamily=fam,
                tags=item.get("tags", []),
                expected_concepts=item.get("expected_concepts", []),
                ideal_answer=ideal,
                idealAnswer=ideal,
                explanation=item.get("explanation")
            )
            chosen.append(model)
            return model

        # Pass 1: Fresh (not recent), topic < 2, distinct family, distinct concept
        for item in shuffled:
            if len(chosen) >= count:
                break
            if can_accept(item, check_recent=True, max_topic=2, check_family=True, check_concept=True):
                add_question(item)

        # Pass 2: Fresh, topic < 2, distinct family
        for item in shuffled:
            if len(chosen) >= count:
                break
            if can_accept(item, check_recent=True, max_topic=2, check_family=True, check_concept=False):
                add_question(item)

        # Pass 3: Fresh, topic < 2
        for item in shuffled:
            if len(chosen) >= count:
                break
            if can_accept(item, check_recent=True, max_topic=2, check_family=False, check_concept=False):
                add_question(item)

        # Pass 4: Fresh, any topic
        for item in shuffled:
            if len(chosen) >= count:
                break
            if can_accept(item, check_recent=True, max_topic=99, check_family=False, check_concept=False):
                add_question(item)

        # Pass 5: Allow recent if pool exhausted, topic < 2, not used in current session
        for item in shuffled:
            if len(chosen) >= count:
                break
            if can_accept(item, check_recent=False, max_topic=2, check_family=False, check_concept=False):
                add_question(item)

        # Pass 6: Any question from pool not used in current session
        for item in shuffled:
            if len(chosen) >= count:
                break
            if can_accept(item, check_recent=False, max_topic=99, check_family=False, check_concept=False):
                add_question(item)

        return chosen

    @classmethod
    def generate_interview_questions(
        cls, 
        candidate_skills: List[str], 
        projects: Optional[List[Dict[str, Any]]] = None,
        recent_question_ids: Optional[List[str]] = None,
        recent_question_fingerprints: Optional[List[str]] = None
    ) -> List[QuestionModel]:
        """
        Strict 13-Question Structured Generator:
        - Q1: Exactly 1 Fixed Introduction Question ("Tell me about yourself.")
        - Q2–Q4: Exactly 3 Project-Based Questions
        - Q5–Q9: Exactly 5 Skill-Based Technical Questions (Multi-skill fair distribution & semantic diversity)
        - Q10–Q11: Exactly 2 Pseudocode MCQ Questions (Language-independent)
        - Q12–Q13: Exactly 2 Dynamic MySQL SQL Coding Questions
        = Exactly 13 Total Questions
        """
        recent_ids = set(recent_question_ids or [])
        recent_fps = set(recent_question_fingerprints or [])

        if not candidate_skills:
            candidate_skills = ["Java", "Python", "Data Structures"]

        selected_questions: List[QuestionModel] = []
        used_ids = set()
        used_texts = set()
        used_fingerprints = set()

        # =========================================================================
        # 1. Q1: FIXED INTRODUCTION QUESTION
        # =========================================================================
        intro_q = QuestionModel(
            id="INTRO_001",
            skill="Introduction",
            difficulty="easy",
            type=QuestionType.INTRODUCTION,
            question="Tell me about yourself.",
            expected_concepts=["Professional Background", "Key Skills", "Project Experience", "Career Goals"],
            ideal_answer="A concise 1-2 minute introduction covering background, technical passions, relevant experience, and key strengths."
        )
        selected_questions.append(intro_q)
        used_ids.add(intro_q.id)
        used_texts.add(normalize_question_text(intro_q.question))
        used_fingerprints.add(create_question_fingerprint(intro_q))

        # =========================================================================
        # 2. SELECT EXACTLY 3 PROJECT QUESTIONS (Q2–Q4)
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
                used_texts.add(normalize_question_text(pq.question))
                used_fingerprints.add(create_question_fingerprint(pq))
        else:
            raw_proj_pool = cls.load_project_questions()
            shuffled_proj_pool = cls.shuffle_list(raw_proj_pool)

            fresh_pool = [q for q in shuffled_proj_pool if q["id"] not in recent_ids]
            candidate_pool = fresh_pool if len(fresh_pool) >= 3 else shuffled_proj_pool

            for item in candidate_pool:
                if len(project_q_models) >= 3:
                    break
                norm_t = normalize_question_text(item["question"])
                if item["id"] not in used_ids and norm_t not in used_texts:
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
                    used_texts.add(norm_t)
                    used_fingerprints.add(create_question_fingerprint(item))

        selected_questions.extend(project_q_models[:3])

        # =========================================================================
        # 3. SELECT EXACTLY 5 TECHNICAL QUESTIONS (Q5–Q9)
        # Multi-skill Fair Slot Distribution + Semantic Diversity Selection
        # =========================================================================
        tech_q_models: List[QuestionModel] = []
        slot_distribution = cls.distribute_question_slots(candidate_skills, total_count=5)
        topic_counts: Dict[str, int] = {}
        used_families: set = set()
        used_concepts: set = set()

        for skill_name, slot_count in slot_distribution.items():
            if len(tech_q_models) >= 5:
                break
            raw_skill_qs = cls.load_skill_questions(skill_name)
            chosen_skill_qs = cls.select_diverse_questions(
                questions_pool=raw_skill_qs,
                count=slot_count,
                used_ids=used_ids,
                used_fingerprints=used_fingerprints,
                used_texts=used_texts,
                recent_ids=recent_ids,
                recent_fingerprints=recent_fps,
                topic_counts=topic_counts,
                used_families=used_families,
                used_concepts=used_concepts
            )
            tech_q_models.extend(chosen_skill_qs)

        # Fallback if any slots remain unfilled
        if len(tech_q_models) < 5:
            remaining_slots = 5 - len(tech_q_models)
            for skill_name in candidate_skills:
                if remaining_slots <= 0:
                    break
                raw_skill_qs = cls.load_skill_questions(skill_name)
                extra_qs = cls.select_diverse_questions(
                    questions_pool=raw_skill_qs,
                    count=remaining_slots,
                    used_ids=used_ids,
                    used_fingerprints=used_fingerprints,
                    used_texts=used_texts,
                    recent_ids=set(),
                    recent_fingerprints=set(),
                    topic_counts=topic_counts,
                    used_families=used_families,
                    used_concepts=used_concepts
                )
                tech_q_models.extend(extra_qs)
                remaining_slots -= len(extra_qs)

        selected_questions.extend(tech_q_models[:5])

        # =========================================================================
        # 4. SELECT EXACTLY 2 LANGUAGE-INDEPENDENT PSEUDOCODE QUESTIONS (Q10–Q11)
        # =========================================================================
        pseudo_q_models = cls.get_dynamic_pseudocode_questions(count=2, recent_ids=list(recent_ids), used_ids=used_ids)
        for pq in pseudo_q_models:
            used_ids.add(pq.id)
            used_texts.add(normalize_question_text(f"{pq.question}_{pq.pseudocode or pq.code_snippet or pq.id}"))
        selected_questions.extend(pseudo_q_models)

        # =========================================================================
        # 5. SELECT EXACTLY 2 DYNAMIC SQL CODING QUESTIONS (Q12–Q13)
        # =========================================================================
        sql_q_models = cls.get_dynamic_sql_questions(count=2, recent_ids=list(recent_ids), used_ids=used_ids)
        for sq in sql_q_models:
            used_ids.add(sq.id)
            used_texts.add(normalize_question_text(sq.question))
        selected_questions.extend(sql_q_models)

        # =========================================================================
        # 6. FINAL VALIDATION (Enforce strict 1 + 3 + 5 + 2 + 2 = 13 Question Set)
        # =========================================================================
        is_valid, validation_msg = cls.validate_question_set(selected_questions, candidate_skills)
        if not is_valid:
            logger.error(f"Critical question validation failure: {validation_msg}")
            raise ValueError(f"Invalid question set generated: {validation_msg}")

        logger.info(f"Generated 13-Question Interview Set. Q1: {selected_questions[0].id}, Q10: {selected_questions[9].id}, Q11: {selected_questions[10].id}, Q12: {selected_questions[11].id}, Q13: {selected_questions[12].id}")
        return selected_questions

    @staticmethod
    def validate_technical_question_bank(skills_dir: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        Validates all 74 skill question banks:
        - Every file exists and is valid JSON
        - >= 15 questions per skill
        - Non-empty metadata: id, skill, question, difficulty, topic, concept, questionFamily, tags, idealAnswer, expected_concepts
        - 100% unique question IDs across all banks
        - No unreplaced template placeholders (e.g. {skill})
        """
        target_dir = skills_dir or SKILLS_DIR
        errors: List[str] = []
        all_ids: Dict[str, str] = {}

        for category, skills in CATEGORIZED_SKILLS.items():
            for skill in skills:
                s_lower = skill.strip().lower()
                filename = SKILL_FILENAME_MAP.get(s_lower)
                if not filename:
                    filename = s_lower.replace(' ', '').replace('.', '').replace('/', '').replace('#', 'sharp') + ".json"

                filepath = os.path.join(target_dir, filename)
                if not os.path.exists(filepath):
                    errors.append(f"Missing question bank file for skill '{skill}': {filename}")
                    continue

                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        q_list = json.load(f)
                except Exception as e:
                    errors.append(f"Failed to parse JSON for skill '{skill}' ({filename}): {e}")
                    continue

                if not isinstance(q_list, list):
                    errors.append(f"Question bank for '{skill}' is not a JSON array")
                    continue

                if len(q_list) < 15:
                    errors.append(f"Skill '{skill}' has only {len(q_list)} questions (< 15 required)")

                for idx, q in enumerate(q_list):
                    qid = q.get("id")
                    if not qid:
                        errors.append(f"Skill '{skill}' question #{idx} missing 'id'")
                    else:
                        if qid in all_ids:
                            errors.append(f"Duplicate question ID '{qid}' found in '{skill}' (already in '{all_ids[qid]}')")
                        else:
                            all_ids[qid] = skill

                    for field in ["question", "difficulty", "topic", "concept", "questionFamily", "idealAnswer", "expected_concepts", "tags"]:
                        val = q.get(field)
                        if val is None or (isinstance(val, (str, list)) and len(val) == 0):
                            errors.append(f"Skill '{skill}' question '{qid}' missing or empty field '{field}'")

                    qtext = q.get("question", "")
                    if re.search(r"\{(?:skill|topic|concept|difficulty|question|name)\}", qtext, re.IGNORECASE):
                        errors.append(f"Skill '{skill}' question '{qid}' contains unreplaced template placeholder: {qtext}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_pseudocode_question(q_dict_or_model: Any) -> bool:
        """
        Validates that a pseudocode question is strictly language-independent,
        has exactly 4 options with valid IDs, a valid correct option,
        and does not contain language-specific syntax or keywords.
        """
        forbidden_regex = [
            r"\bSystem\.out\b",
            r"\bconsole\.log\b",
            r"\bprint\s*\(",
            r"\bprintf\s*\(",
            r"\bcout\s*<<",
            r"\bcin\s*>>",
            r"\bpublic\s+class\b",
            r"\bpublic\s+static\b",
            r"\bdef\s+[a-zA-Z_]",
            r"\b#include\b",
            r"\bimport\s+[a-zA-Z_]",
            r"\bfrom\s+[a-zA-Z_]+\s+import\b",
            r"\bstd::",
            r"\bint\s+main\b",
            r"\bchar\*",
            r"\bNone\b",
            r"\bnullptr\b",
            r"\bvector<",
            r"\barraylist\b",
            r"\blist<",
            r"\bhashmap<",
            r"\bmap<",
            r"\bdict\(",
            r"\bset\(",
            r"\blet\s+",
            r"\bvar\s+",
            r"\bconst\s+",
            r"\bfn\b",
            r"\bfunc\b"
        ]

        if isinstance(q_dict_or_model, QuestionModel):
            if q_dict_or_model.type not in [QuestionType.PSEUDOCODE, QuestionType.PSEUDOCODE_MCQ]:
                return False
            if q_dict_or_model.language_independent is not True and q_dict_or_model.languageIndependent is not True:
                return False
            options = q_dict_or_model.options
            correct_id = q_dict_or_model.correctOptionId or q_dict_or_model.correct_option_id or q_dict_or_model.correct_answer
            content_to_check = f"{q_dict_or_model.question} {q_dict_or_model.pseudocode or ''} {q_dict_or_model.code_snippet or ''} {q_dict_or_model.input or ''} {q_dict_or_model.input_description or ''}"
        elif isinstance(q_dict_or_model, dict):
            q_type = str(q_dict_or_model.get("type", "")).lower() or str(q_dict_or_model.get("questionType", "")).lower()
            if q_type not in ["pseudocode", "pseudocode_mcq"]:
                return False
            if q_dict_or_model.get("language_independent") is not True and q_dict_or_model.get("languageIndependent") is not True:
                return False
            options = q_dict_or_model.get("options")
            correct_id = q_dict_or_model.get("correctOptionId") or q_dict_or_model.get("correct_option_id") or q_dict_or_model.get("correct_answer")
            content_to_check = f"{q_dict_or_model.get('question', '')} {q_dict_or_model.get('pseudocode', '')} {q_dict_or_model.get('code_snippet', '')} {q_dict_or_model.get('input', '')} {q_dict_or_model.get('input_description', '')}"
        else:
            return False

        # Validate 4 options if options are present
        if options is not None:
            if not isinstance(options, list) or len(options) != 4:
                return False
            if isinstance(options[0], dict):
                opt_ids = [str(opt.get("id", "")) for opt in options]
                if opt_ids != ["A", "B", "C", "D"]:
                    return False
                if correct_id and correct_id not in opt_ids:
                    return False

        for pattern in forbidden_regex:
            if re.search(pattern, content_to_check, re.IGNORECASE):
                return False

        return True

    @classmethod
    def get_dynamic_pseudocode_questions(
        cls,
        count: int = 2,
        recent_ids: Optional[List[str]] = None,
        used_ids: Optional[set] = None
    ) -> List[QuestionModel]:
        """
        Randomly selects exactly 2 distinct, language-independent pseudocode MCQ questions
        from the general pseudocode question bank, prioritizing distinct categories.
        """
        recent = set(recent_ids or [])
        used = used_ids if used_ids is not None else set()

        raw_pseudo = cls.load_pseudocode_questions()
        valid_pool = [q for q in raw_pseudo if cls.validate_pseudocode_question(q)]

        if not valid_pool:
            logger.warning("No valid pseudocode questions found in pool, using raw pool")
            valid_pool = raw_pseudo

        # Shuffle pool
        shuffled = cls.shuffle_list(valid_pool)

        # Prioritize unseen and distinct categories
        chosen: List[Dict[str, Any]] = []
        chosen_categories = set()

        # Pass 1: Unseen in recent_ids and used_ids with distinct categories
        for q in shuffled:
            if len(chosen) >= count:
                break
            qid = q.get("id")
            cat = q.get("category", "GENERAL")
            if qid not in recent and qid not in used and cat not in chosen_categories:
                chosen.append(q)
                chosen_categories.add(cat)

        # Pass 2: Unseen in used_ids
        for q in shuffled:
            if len(chosen) >= count:
                break
            qid = q.get("id")
            if qid not in used and q not in chosen:
                chosen.append(q)

        # Pass 3: Any valid questions from pool
        for q in shuffled:
            if len(chosen) >= count:
                break
            if q not in chosen:
                chosen.append(q)

        selected_models: List[QuestionModel] = []
        for item in chosen[:count]:
            correct_opt = item.get("correctOptionId") or item.get("correct_option_id") or item.get("correct_answer")
            code_snip = item.get("pseudocode") or item.get("code_snippet")
            input_val = item.get("input") or item.get("input_description")
            selected_models.append(
                QuestionModel(
                    id=item["id"],
                    category=item.get("category", "LOGIC"),
                    topic=item.get("topic", "Logic & Algorithms"),
                    skill="Logic & Algorithms",
                    difficulty=item.get("difficulty", "medium"),
                    type=QuestionType.PSEUDOCODE,
                    question_type="PSEUDOCODE_MCQ",
                    questionType="PSEUDOCODE_MCQ",
                    question=item["question"],
                    prompt=item.get("prompt"),
                    input=input_val,
                    input_description=input_val,
                    expected_output_description=item.get("expected_output_description"),
                    example=item.get("example"),
                    pseudocode=code_snip,
                    code_snippet=code_snip,
                    language_independent=True,
                    languageIndependent=True,
                    supported_languages=["language-independent"],
                    answer_mode="mcq",
                    answerMode="mcq",
                    options=item.get("options"),
                    correct_answer=correct_opt,
                    correct_option_id=correct_opt,
                    correctOptionId=correct_opt,
                    explanation=item.get("explanation"),
                    score=item.get("score", 1),
                    expected_concepts=item.get("expected_concepts", ["Logical Reasoning", "Algorithm Tracing"]),
                    ideal_answer=item.get("ideal_answer", "")
                )
            )

        return selected_models

    @classmethod
    def get_dynamic_sql_questions(
        cls, 
        count: int = 2, 
        recent_ids: Optional[List[str]] = None,
        used_ids: Optional[set] = None
    ) -> List[QuestionModel]:
        """
        Dynamically selects randomized SQL questions from the question bank.
        """
        recent_set = set(recent_ids or [])
        used_set = set(used_ids or [])
        
        raw_sql_pool = SqlService.load_sql_questions()
        shuffled_sql_pool = cls.shuffle_list(raw_sql_pool)

        fresh_sql = [q for q in shuffled_sql_pool if q["id"] not in recent_set and q["id"] not in used_set]
        sql_candidates = fresh_sql if len(fresh_sql) >= count else shuffled_sql_pool

        sql_q_models: List[QuestionModel] = []
        for sql_item in sql_candidates:
            if len(sql_q_models) >= count:
                break
            if sql_item["id"] not in [q.id for q in sql_q_models]:
                sql_q_models.append(
                    QuestionModel(
                        id=sql_item["id"],
                        skill="MySQL Database",
                        difficulty=sql_item.get("difficulty", "Medium").lower(),
                        type=QuestionType.SQL,
                        question=sql_item["description"],
                        title=sql_item.get("title"),
                        topic=sql_item.get("topic"),
                        description=sql_item["description"],
                        tables=sql_item["tables"],
                        expected_query=sql_item["expected_query"],
                        expected_output=sql_item.get("expected_output"),
                        expected_result=sql_item.get("expected_result"),
                        explanation=sql_item.get("explanation"),
                        expected_concepts=[sql_item.get("topic", "SQL"), "Relational Schema", "Query Optimization"],
                        ideal_answer=sql_item["expected_query"]
                    )
                )

        return sql_q_models

    @staticmethod
    def validate_question_set(questions: List[QuestionModel], candidate_skills: List[str]) -> Tuple[bool, str]:
        """
        Validates the strict 1 + 3 + 5 + 2 + 2 = 13 question distribution contract:
        - Exactly 13 total questions
        - Exactly 1 Introduction question (Q1: "Tell me about yourself.")
        - Exactly 3 Project questions
        - Exactly 5 Technical skill questions
        - Exactly 2 Pseudocode questions (language-independent)
        - Exactly 2 SQL coding questions
        - 100% unique question IDs
        - 100% unique question texts
        - Q12.id != Q13.id
        - For both SQL questions: exactly 2 tables, each >= 5 columns and >= 5 rows
        """
        if len(questions) != 13:
            return False, f"Expected exactly 13 questions, got {len(questions)}"

        intro_qs = [q for q in questions if q.type == QuestionType.INTRODUCTION]
        project_qs = [q for q in questions if q.type == QuestionType.PROJECT]
        tech_qs = [q for q in questions if q.type == QuestionType.TECHNICAL]
        pseudo_qs = [q for q in questions if q.type in [QuestionType.PSEUDOCODE, QuestionType.PSEUDOCODE_MCQ]]
        sql_qs = [q for q in questions if q.type == QuestionType.SQL]

        if len(intro_qs) != 1 or questions[0].question.strip() != "Tell me about yourself.":
            return False, "Q1 must be the fixed introduction question 'Tell me about yourself.'"

        if len(project_qs) != 3:
            return False, f"Expected exactly 3 project questions, got {len(project_qs)}"
        if len(tech_qs) != 5:
            return False, f"Expected exactly 5 technical skill questions, got {len(tech_qs)}"
        if len(pseudo_qs) != 2:
            return False, f"Expected exactly 2 pseudocode questions, got {len(pseudo_qs)}"
        if len(sql_qs) != 2:
            return False, f"Expected exactly 2 SQL questions, got {len(sql_qs)}"

        q_ids = [q.id for q in questions]
        if len(set(q_ids)) != 13:
            return False, f"Duplicate question IDs detected: {q_ids}"

        content_keys = [
            f"{q.question.strip()}_{q.pseudocode.strip() if q.pseudocode else (q.code_snippet.strip() if q.code_snippet else q.id)}"
            if q.type in [QuestionType.PSEUDOCODE, QuestionType.PSEUDOCODE_MCQ]
            else q.question.strip()
            for q in questions
        ]
        if len(set(content_keys)) != 13:
            return False, "Duplicate question texts detected in session"

        # Verify language independence of pseudocode questions
        for pq in pseudo_qs:
            if not QuestionService.validate_pseudocode_question(pq):
                return False, f"Pseudocode Question '{pq.id}' is not strictly language-independent"

        if sql_qs[0].id == sql_qs[1].id:
            return False, f"Q12 and Q13 must have different question IDs (got duplicate: {sql_qs[0].id})"

        # Validate SQL tables
        for sql_q in sql_qs:
            tables = sql_q.tables or []
            if len(tables) != 2:
                return False, f"SQL Question '{sql_q.id}' must have exactly 2 tables, got {len(tables)}"
            for tbl in tables:
                cols = tbl.get("columns", [])
                rows = tbl.get("rows", [])
                if len(cols) < 5:
                    return False, f"SQL Question '{sql_q.id}' table '{tbl.get('name')}' has {len(cols)} columns (min 5 required)"
                if len(rows) < 5:
                    return False, f"SQL Question '{sql_q.id}' table '{tbl.get('name')}' has {len(rows)} rows (min 5 required)"

        return True, "Valid"
