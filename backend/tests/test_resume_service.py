import pytest
from app.services.resume_service import ResumeService

def test_clean_text():
    raw = "Hello   World!\n\nThis is\ta   test.\n"
    cleaned = ResumeService.clean_text(raw)
    assert cleaned == "Hello World!\nThis is a test."

def test_extract_skills():
    resume_text = "Proficient in Python, Java, React, Docker, MySQL and AWS cloud infrastructure."
    skills = ResumeService.extract_skills(resume_text)
    assert "Python" in skills
    assert "Java" in skills
    assert "React" in skills
    assert "Docker" in skills
    assert "MySQL" in skills
    assert "AWS" in skills

def test_extract_projects():
    resume_text = """
    TECHNICAL SKILLS
    Python, Java, React, MySQL

    PROJECTS
    Library Management System
    Built a web portal using Java, Spring Boot, React and MySQL to manage book lending.
    
    E-Commerce API
    Developed REST endpoints using Python and MySQL.
    """
    skills = ResumeService.extract_skills(resume_text)
    projects = ResumeService.extract_projects(resume_text, skills)
    
    assert len(projects) >= 1
    assert any("Library" in p["name"] or "E-Commerce" in p["name"] for p in projects)
