import os
import re
from typing import Dict, List, Any
from pypdf import PdfReader
from docx import Document
from app.services.question_service import TAXONOMY_SKILLS
from app.utils.logger import logger

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
        # Remove extra whitespace and special characters while preserving readable text
        cleaned = re.sub(r'[\r\t]', ' ', raw_text)
        cleaned = re.sub(r' +', ' ', cleaned)
        cleaned = re.sub(r'\n+', '\n', cleaned)
        return cleaned.strip()

    @classmethod
    def parse_resume(cls, file_path: str, filename: str) -> Dict[str, Any]:
        text = cls.extract_text_from_file(file_path, filename)
        
        # 1. Skill Extraction matching controlled taxonomy
        extracted_skills = cls.extract_skills(text)

        # 2. Project & Technology Extraction
        extracted_projects = cls.extract_projects(text, extracted_skills)

        return {
            "skills": extracted_skills,
            "projects": extracted_projects,
            "raw_text_length": len(text)
        }

    @staticmethod
    def extract_skills(text: str) -> List[str]:
        found_skills = set()
        text_lower = text.lower()

        for skill in TAXONOMY_SKILLS:
            # Word boundary pattern search to prevent false positives (e.g., C in Cat)
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill)

        # Priority fallback defaults if resume is brief
        if not found_skills:
            found_skills = {"Java", "SQL", "Git"}

        return sorted(list(found_skills))

    @staticmethod
    def extract_projects(text: str, extracted_skills: List[str]) -> List[Dict[str, Any]]:
        projects = []
        lines = text.split("\n")
        
        # Look for project section headers
        in_project_section = False
        current_project_name = None
        current_techs = set()

        project_keywords = ["projects", "personal projects", "academic projects", "key projects"]

        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            # Check for section header
            if any(kw in line_clean.lower() for kw in project_keywords) and len(line_clean) < 40:
                in_project_section = True
                continue

            if in_project_section:
                # Check for new project heading or bullet point
                if re.match(r'^[•\-\*]?\s*([A-Z0-9\s\-_]{3,40}):?', line_clean) and not any(kw in line_clean.lower() for kw in ["experience", "education", "skills"]):
                    if current_project_name and current_techs:
                        projects.append({
                            "name": current_project_name,
                            "technologies": list(current_techs)
                        })
                    
                    current_project_name = line_clean.strip(":-•* ")
                    current_techs = set()

                # Extract technologies mentioned in line
                for skill in extracted_skills:
                    if re.search(r'\b' + re.escape(skill.lower()) + r'\b', line_clean.lower()):
                        current_techs.add(skill)

                # Stop section if reaching next major heading
                if any(hdr in line_clean.lower() for hdr in ["experience", "education", "certifications", "achievements"]) and len(line_clean) < 40:
                    break

        if current_project_name:
            projects.append({
                "name": current_project_name,
                "technologies": list(current_techs) if current_techs else extracted_skills[:3]
            })

        # Fallback default project if structure parsing didn't find specific titles
        if not projects:
            projects.append({
                "name": "Software Application Project",
                "technologies": extracted_skills[:4] if extracted_skills else ["Java", "React", "MySQL"]
            })

        return projects
