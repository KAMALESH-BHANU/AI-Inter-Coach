import os
import re
from typing import Dict, List, Any, Optional, Set
from pypdf import PdfReader
from docx import Document
from app.services.question_service import TAXONOMY_SKILLS
from app.utils.logger import logger

# Canonical section definitions for robust resume segmentation
SECTION_DEFINITIONS = {
    "PROJECTS": [
        "projects", "personal projects", "academic projects", "key projects",
        "relevant projects", "project work", "capstone project", "selected projects",
        "technical projects", "side projects", "notable projects", "my projects"
    ],
    "CERTIFICATIONS": [
        "certifications", "certificates", "licenses & certifications", "licenses and certifications",
        "online courses", "accreditations", "training & certifications", "certifications & courses",
        "professional certifications", "certifications and licenses", "courses & certifications"
    ],
    "SKILLS": [
        "skills", "technical skills", "core competencies", "technologies",
        "programming languages", "tools & frameworks", "areas of expertise",
        "technical proficiencies", "technical expertise", "skills & tools",
        "technical stack", "skills & abilities"
    ],
    "EXPERIENCE": [
        "experience", "work experience", "employment history", "professional experience",
        "internships", "work history", "career history", "industry experience",
        "relevant experience"
    ],
    "EDUCATION": [
        "education", "academic background", "educational qualifications", "degrees",
        "academic history", "qualification", "qualifications", "academic credentials"
    ],
    "ACHIEVEMENTS": [
        "achievements", "honors & awards", "honors and awards", "accomplishments",
        "awards", "key achievements", "competitions", "hackathons", "honors"
    ],
    "PUBLICATIONS": [
        "publications", "papers", "research papers", "patents", "conference publications",
        "whitepapers"
    ],
    "SUMMARY": [
        "summary", "professional summary", "profile", "about me", "objective",
        "career objective", "executive summary", "personal summary"
    ],
    "COURSEWORK": [
        "coursework", "relevant courses", "courses", "relevant coursework"
    ],
    "INTERESTS": [
        "interests", "hobbies", "extracurricular activities", "activities", "leadership"
    ]
}

# Strict blacklist of section titles and generic terms that MUST NEVER be project names
BLACKLISTED_SECTION_HEADINGS: Set[str] = {
    "CERTIFICATIONS", "CERTIFICATION", "CERTIFICATES", "CERTIFICATE",
    "SKILLS", "SKILL", "TECHNICAL SKILLS", "CORE SKILLS", "TECHNOLOGIES", "TECH STACK",
    "EDUCATION", "ACADEMICS", "QUALIFICATIONS", "DEGREES",
    "EXPERIENCE", "WORK EXPERIENCE", "EMPLOYMENT", "INTERNSHIPS", "WORK HISTORY",
    "ACHIEVEMENTS", "ACHIEVEMENT", "HONORS", "AWARDS", "HONORS & AWARDS",
    "PUBLICATIONS", "PUBLICATION", "PATENTS", "RESEARCH",
    "COURSEWORK", "COURSES", "RELEVANT COURSES",
    "INTERESTS", "HOBBIES", "ACTIVITIES", "LEADERSHIP",
    "SUMMARY", "OBJECTIVE", "PROFILE", "ABOUT ME", "ABOUT", "CAREER OBJECTIVE",
    "DECLARATION", "PERSONAL DETAILS", "CONTACT", "REFERENCES", "LANGUAGES", "STRENGTHS",
    "PROJECT", "PROJECTS", "PERSONAL PROJECTS", "ACADEMIC PROJECTS", "KEY PROJECTS"
}

GENERIC_PROJECT_WORDS: Set[str] = {
    "project", "projects", "system", "application", "app", "title", "name",
    "description", "technologies", "tech stack", "tools", "link", "duration",
    "github", "live link", "overview", "features", "details", "work"
}

class ResumeService:
    @classmethod
    def extract_text_from_file(cls, file_path: str, filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        text = ""
        try:
            if ext == ".pdf":
                reader = PdfReader(file_path)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            elif ext in [".docx", ".doc"]:
                doc = Document(file_path)
                for para in doc.paragraphs:
                    text += para.text + "\n"
            elif ext == ".txt":
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            else:
                raise ValueError(f"Unsupported file format: {ext}")
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {e}")
            raise e

        return cls.clean_text(text)

    @staticmethod
    def clean_text(raw_text: str) -> str:
        cleaned = re.sub(r'[\r\t]', ' ', raw_text)
        cleaned = re.sub(r' +', ' ', cleaned)
        cleaned = re.sub(r'\n+', '\n', cleaned)
        return cleaned.strip()

    @classmethod
    def is_section_heading(cls, line: str) -> Optional[str]:
        """
        Determines if a line is a resume section heading and returns canonical section key.
        """
        clean = re.sub(r'^[#*\-•\d\.\:\s]+', '', line).strip()
        clean = re.sub(r'[:\s#*]+$', '', clean).strip()
        clean_lower = clean.lower()

        if len(clean) == 0 or len(clean) > 45:
            return None

        for section, keywords in SECTION_DEFINITIONS.items():
            for kw in keywords:
                if clean_lower == kw or clean_lower == f"{kw}:" or clean_lower == f"my {kw}":
                    return section
        return None

    @classmethod
    def segment_sections(cls, text: str) -> Dict[str, List[str]]:
        """
        Segments raw resume text into categorized sections (PROJECTS, CERTIFICATIONS, SKILLS, etc.)
        """
        sections: Dict[str, List[str]] = {"HEADER": []}
        current_section = "HEADER"
        lines = text.split("\n")

        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            detected_sec = cls.is_section_heading(line_clean)
            if detected_sec:
                current_section = detected_sec
                if current_section not in sections:
                    sections[current_section] = []
                continue

            if current_section not in sections:
                sections[current_section] = []
            sections[current_section].append(line_clean)

        return sections

    @classmethod
    def parse_resume(cls, file_path: str, filename: str) -> Dict[str, Any]:
        text = cls.extract_text_from_file(file_path, filename)
        sections = cls.segment_sections(text)

        # 1. Skill Extraction
        extracted_skills = cls.extract_skills(text)

        # 2. Project Extraction (Strictly from PROJECTS section, zero section-header false positives)
        extracted_projects = cls.extract_projects(text, extracted_skills, sections)

        # 3. Certifications Extraction
        extracted_certifications = cls.extract_certifications(text, extracted_skills, sections)

        return {
            "skills": extracted_skills,
            "projects": extracted_projects,
            "certifications": extracted_certifications,
            "sections": {k: len(v) for k, v in sections.items()},
            "raw_text_length": len(text)
        }

    @staticmethod
    def extract_skills(text: str) -> List[str]:
        found_skills = set()
        text_lower = text.lower()

        for skill in TAXONOMY_SKILLS:
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill)

        if not found_skills:
            found_skills = {"Java", "SQL", "Git"}

        return sorted(list(found_skills))

    @classmethod
    def is_valid_project_name(cls, name: str) -> bool:
        """
        Validates that a string is a genuine project name and not a section heading, metadata line, or generic word.
        """
        if not name or len(name.strip()) < 3:
            return False

        stripped = name.strip()
        stripped_lower = stripped.lower()
        clean_upper = re.sub(r'[^A-Z0-9\s]', ' ', stripped.upper()).strip()
        clean_upper = re.sub(r'\s+', ' ', clean_upper)

        # Check exact blacklist match
        if clean_upper in BLACKLISTED_SECTION_HEADINGS:
            return False

        # Check if name is purely any single generic word
        if clean_upper.lower() in GENERIC_PROJECT_WORDS:
            return False

        # Check if line looks like a known section header
        if cls.is_section_heading(name) is not None:
            return False

        # Check if line starts with metadata prefixes
        metadata_prefixes = [
            "github:", "github.com", "http:", "https:", "link:", "url:", "live:", "demo:",
            "duration:", "date:", "dates:", "timeline:", "period:",
            "technologies:", "tech stack:", "tools:", "skills:", "built with:", "stack:",
            "role:", "responsibilities:", "key features:", "features:"
        ]
        if any(stripped_lower.startswith(prefix) for prefix in metadata_prefixes):
            return False

        # Check if name is purely a comma-separated list of technologies (e.g., "Java, Spring Boot, MySQL")
        items = [i.strip() for i in re.split(r'[,/|]', stripped) if i.strip()]
        if len(items) > 1:
            skill_match_count = sum(1 for item in items if any(item.lower() == s.lower() for s in TAXONOMY_SKILLS))
            if skill_match_count / len(items) >= 0.7:
                return False

        # If name is a single skill alone (e.g. "Java" or "Python")
        if any(stripped_lower == s.lower() for s in TAXONOMY_SKILLS):
            return False

        # Check if name is solely a link, date, or contact info
        if re.match(r'^(https?://|www\.|github\.com|linkedin\.com)', stripped, re.I):
            return False
        if re.match(r'^(\d{4}|\w+\s+\d{4})\s*[-–—]\s*(\d{4}|\w+\s+\d{4}|present)$', stripped, re.I):
            return False

        return True

    @classmethod
    def extract_projects(
        cls, 
        text: str, 
        extracted_skills: List[str], 
        sections: Optional[Dict[str, List[str]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extracts valid candidate projects strictly from project sections.
        Returns empty list [] if no valid projects exist (never produces fake fallback projects).
        """
        if sections is None:
            sections = cls.segment_sections(text)

        project_lines = sections.get("PROJECTS", [])
        if not project_lines:
            return []

        projects: List[Dict[str, Any]] = []
        current_project: Optional[Dict[str, Any]] = None

        for line in project_lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            # Strip bullet or numbering prefix
            stripped_line = re.sub(r'^[•\-\*\d\.\:\s]+', '', line_clean).strip()
            stripped_lower = stripped_line.lower()

            # Extract optional inline URL
            url_match = re.search(r'(https?://[^\s\)]+|github\.com/[^\s\)]+)', line_clean, re.I)
            inline_url = url_match.group(1) if url_match else None

            # Extract optional duration
            dur_match = re.search(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{4})[^\n\|]*?(?:Present|\d{4}))', line_clean, re.I)
            inline_dur = dur_match.group(1).strip() if dur_match else None

            # Extract inline technologies from the whole line
            inline_techs = set()
            for skill in TAXONOMY_SKILLS:
                if re.search(r'\b' + re.escape(skill.lower()) + r'\b', line_clean.lower()):
                    inline_techs.add(skill)

            # Check for metadata line prefixes (URL, duration, key words)
            is_metadata_prefix = any(stripped_lower.startswith(p) for p in [
                "github:", "github.com", "http:", "https:", "link:", "url:", "live:", "demo:",
                "duration:", "date:", "dates:", "timeline:", "period:",
                "technologies:", "tech stack:", "tools:", "skills:", "built with:", "stack:",
                "role:", "responsibilities:", "features:"
            ]) or (dur_match and len(stripped_line) < 35 and not ('|' in stripped_line or '(' in stripped_line))

            # Determine title candidate and split inline metadata
            is_title_candidate = False
            candidate_name = stripped_line

            if not is_metadata_prefix:
                if '|' in stripped_line:
                    parts = stripped_line.split('|')
                    candidate_name = parts[0].strip()
                    is_title_candidate = True
                elif '(' in stripped_line and ')' in stripped_line:
                    parts = stripped_line.split('(')
                    candidate_name = parts[0].strip()
                    is_title_candidate = True
                elif ' - ' in stripped_line and not stripped_line.startswith('http'):
                    parts = stripped_line.split(' - ')
                    if len(parts[0].strip()) < 40 and not any(kw in parts[0].lower() for kw in ["built", "implemented", "developed", "using", "created"]):
                        candidate_name = parts[0].strip()
                        is_title_candidate = True
                else:
                    # Check if line is purely a comma-separated list of skills (e.g. "Java, Spring Boot, MySQL")
                    items = [i.strip() for i in re.split(r'[,/]', stripped_line) if i.strip()]
                    if len(items) > 1:
                        skill_match_count = sum(1 for item in items if any(item.lower() == s.lower() for s in TAXONOMY_SKILLS))
                        if skill_match_count / len(items) >= 0.7:
                            is_title_candidate = False
                        else:
                            is_title_candidate = len(stripped_line) < 60 and not stripped_line.endswith('.') and not any(
                                verb in stripped_lower for verb in ["built", "developed", "created", "designed", "implemented", "worked on", "managed", "utilized", "integrated"]
                            )
                    else:
                        is_title_candidate = len(stripped_line) < 60 and not stripped_line.endswith('.') and not any(
                            verb in stripped_lower for verb in ["built", "developed", "created", "designed", "implemented", "worked on", "managed", "utilized", "integrated"]
                        )

            # Validate the candidate project name against blacklist & section headers
            if is_title_candidate and cls.is_valid_project_name(candidate_name):
                # Save previous project if valid
                if current_project and cls.is_valid_project_name(current_project["name"]):
                    if not current_project["technologies"]:
                        desc_text = " ".join(current_project["description_lines"]).lower()
                        for s in extracted_skills:
                            if re.search(r'\b' + re.escape(s.lower()) + r'\b', desc_text):
                                current_project["technologies"].append(s)
                    projects.append({
                        "name": current_project["name"],
                        "description": " ".join(current_project["description_lines"]).strip(),
                        "technologies": sorted(list(set(current_project["technologies"]))),
                        "url": current_project.get("url"),
                        "duration": current_project.get("duration")
                    })

                current_project = {
                    "name": candidate_name.strip(":-•* "),
                    "description_lines": [],
                    "technologies": list(inline_techs),
                    "url": inline_url,
                    "duration": inline_dur
                }
            else:
                # Accumulate description, URL, duration, and technologies into current active project
                if current_project:
                    if not is_metadata_prefix and not any(candidate_name.lower() == s.lower() for s in TAXONOMY_SKILLS):
                        current_project["description_lines"].append(line_clean)
                    for skill in inline_techs:
                        if skill not in current_project["technologies"]:
                            current_project["technologies"].append(skill)
                    if inline_url and not current_project.get("url"):
                        current_project["url"] = inline_url
                    if inline_dur and not current_project.get("duration"):
                        current_project["duration"] = inline_dur

        # Save final trailing project
        if current_project and cls.is_valid_project_name(current_project["name"]):
            if not current_project["technologies"]:
                desc_text = " ".join(current_project["description_lines"]).lower()
                for s in extracted_skills:
                    if re.search(r'\b' + re.escape(s.lower()) + r'\b', desc_text):
                        current_project["technologies"].append(s)
            projects.append({
                "name": current_project["name"],
                "description": " ".join(current_project["description_lines"]).strip(),
                "technologies": sorted(list(set(current_project["technologies"]))),
                "url": current_project.get("url"),
                "duration": current_project.get("duration")
            })

        # Strict clean-up: Remove any entry whose name matches a blacklisted section
        final_projects = [
            p for p in projects 
            if cls.is_valid_project_name(p["name"]) and p["name"].upper() not in BLACKLISTED_SECTION_HEADINGS
        ]

        return final_projects

    @classmethod
    def extract_certifications(
        cls, 
        text: str, 
        extracted_skills: List[str], 
        sections: Optional[Dict[str, List[str]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extracts certifications and licenses from the CERTIFICATIONS section and overall resume.
        """
        if sections is None:
            sections = cls.segment_sections(text)

        cert_lines = sections.get("CERTIFICATIONS", [])
        if not cert_lines:
            return []

        certifications: List[Dict[str, Any]] = []

        for line in cert_lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            # Strip bullet prefixes
            item_text = re.sub(r'^[•\-\*\d\.\:\s]+', '', line_clean).strip()
            if len(item_text) < 3:
                continue

            # Skip lines that are just section headers or generic words
            if item_text.upper() in BLACKLISTED_SECTION_HEADINGS:
                continue

            # Extract associated skills/technologies mentioned in certification
            cert_skills = []
            for skill in TAXONOMY_SKILLS:
                if re.search(r'\b' + re.escape(skill.lower()) + r'\b', item_text.lower()):
                    cert_skills.append(skill)

            # Detect credential issuer if present (e.g. NPTEL, Coursera, AWS, Google, Udemy, HackerRank, Oracle)
            issuer = None
            for known_issuer in ["NPTEL", "Coursera", "AWS", "Google", "Microsoft", "Udemy", "HackerRank", "Oracle", "Cisco", "Meta", "IBM", "freeCodeCamp"]:
                if re.search(r'\b' + re.escape(known_issuer) + r'\b', item_text, re.I):
                    issuer = known_issuer
                    break

            certifications.append({
                "name": item_text,
                "issuer": issuer,
                "skills": cert_skills
            })

        return certifications

