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

def test_extract_projects_and_certifications_disambiguation():
    """
    Test 1: Resume containing both Projects and Certifications.
    Verifies that CERTIFICATIONS is NOT classified as a project name,
    and actual projects & certifications are extracted cleanly.
    """
    resume_text = """
    SKILLS
    Java, Spring Boot, MySQL, Python, Git, GitHub, CSS

    PROJECTS
    Library Management System
    Java, Spring Boot, MySQL
    Developed an automated library catalog and book lending portal.

    CERTIFICATIONS
    NPTEL Joy of Computing Python
    Git, GitHub
    """
    skills = ResumeService.extract_skills(resume_text)
    projects = ResumeService.extract_projects(resume_text, skills)
    certifications = ResumeService.extract_certifications(resume_text, skills)

    # 1. Project verification
    assert len(projects) == 1
    assert projects[0]["name"] == "Library Management System"
    assert "Java" in projects[0]["technologies"]
    assert "Spring Boot" in projects[0]["technologies"]
    assert "MySQL" in projects[0]["technologies"]

    # 2. Section header must NEVER be a project name
    assert not any(p["name"].upper() == "CERTIFICATIONS" for p in projects)
    assert not any("CERTIFICATIONS" in p["name"].upper() for p in projects)

    # 3. Certifications verification
    assert len(certifications) >= 1
    assert any("NPTEL" in c["name"] or "Computing Python" in c["name"] for c in certifications)

def test_resume_with_only_certifications_no_projects():
    """
    Test 2: Resume containing only Certifications (zero projects).
    Must return empty projects list [] with NO fake fallback projects.
    """
    resume_text = """
    TECHNICAL SKILLS
    CSS, Git, GitHub, Python

    CERTIFICATIONS
    NPTEL Joy of Computing Python
    AWS Certified Cloud Practitioner
    """
    skills = ResumeService.extract_skills(resume_text)
    projects = ResumeService.extract_projects(resume_text, skills)
    certifications = ResumeService.extract_certifications(resume_text, skills)

    assert len(projects) == 0
    assert len(certifications) >= 2
    assert not any(p["name"].upper() == "CERTIFICATIONS" for p in projects)

def test_multiple_projects_extraction():
    """
    Test 3: Resume containing multiple projects with descriptions and technologies.
    """
    resume_text = """
    TECHNICAL SKILLS
    Java, Python, React, MySQL, Docker, FastAPI

    PROJECTS
    1. E-Commerce Platform | React, Node.js, MySQL
    Built high-throughput checkout service and inventory management.
    GitHub: https://github.com/test/ecommerce

    2. Real-Time Chat System (Python, FastAPI, Docker)
    Implemented WebSockets for live peer-to-peer messaging.
    Duration: Jan 2024 - Mar 2024

    3. AI Resume Analyzer
    Developed NLP parsing pipeline using Python and regular expressions.
    """
    skills = ResumeService.extract_skills(resume_text)
    projects = ResumeService.extract_projects(resume_text, skills)

    assert len(projects) == 3
    names = [p["name"] for p in projects]
    assert "E-Commerce Platform" in names
    assert "Real-Time Chat System" in names
    assert "AI Resume Analyzer" in names

    p1 = next(p for p in projects if p["name"] == "E-Commerce Platform")
    assert "React" in p1["technologies"] or "MySQL" in p1["technologies"]

def test_skills_immediately_after_projects():
    """
    Test 4: Resume containing Skills section immediately after Projects section.
    Ensures SKILLS header does not leak into projects.
    """
    resume_text = """
    PROJECTS
    Portfolio Website
    Created personal portfolio with React and Tailwind.

    SKILLS
    Python, Java, MySQL, Docker, Kubernetes

    EDUCATION
    Bachelor of Technology in Computer Science
    """
    skills = ResumeService.extract_skills(resume_text)
    projects = ResumeService.extract_projects(resume_text, skills)

    assert len(projects) == 1
    assert projects[0]["name"] == "Portfolio Website"
    assert not any(p["name"].upper() in ["SKILLS", "EDUCATION"] for p in projects)

def test_section_heading_format_variants():
    """
    Test 5: Resume with various section heading formats (markdown, colon, title-case).
    """
    resume_text = """
    ### TECHNICAL SKILLS:
    Java, React, SQL

    ## KEY PROJECTS:
    • Inventory Tracking System
    Implemented stock alert algorithm using Java and SQL.

    ## LICENSES & CERTIFICATIONS:
    Oracle Certified Associate, Java SE 8 Programmer
    """
    skills = ResumeService.extract_skills(resume_text)
    projects = ResumeService.extract_projects(resume_text, skills)
    certifications = ResumeService.extract_certifications(resume_text, skills)

    assert len(projects) == 1
    assert "Inventory Tracking System" in projects[0]["name"]
    assert not any("CERTIFICATIONS" in p["name"].upper() for p in projects)
    assert len(certifications) >= 1

