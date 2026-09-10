import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "app" in data

def test_auth_registration_and_login():
    email = "testuser@example.com"
    pwd = "securepassword123"

    # 1. Register
    reg_res = client.post("/api/auth/register", json={
        "email": email,
        "full_name": "Test Candidate",
        "password": pwd,
        "skills": ["Java", "Python"]
    })
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    token = reg_data["access_token"]

    # 2. Get Me
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == email

    # 3. Login
    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": pwd
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

def test_skills_taxonomy():
    res = client.get("/api/questions/skills?search=java")
    assert res.status_code == 200
    skills = res.json()
    assert isinstance(skills, list)
    assert any("Java" in s for s in skills)
