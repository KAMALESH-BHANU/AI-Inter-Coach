import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_interview_lifecycle():
    # 1. Register candidate
    email = "lifecycletest@example.com"
    pwd = "password123"
    reg_res = client.post("/api/auth/register", json={
        "email": email,
        "full_name": "Lifecycle Candidate",
        "password": pwd,
        "skills": ["Java", "Python"]
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Interview
    create_res = client.post("/api/interview/create", json={
        "skills": ["Java", "Python"],
        "projects": [{"name": "E-Commerce App", "description": "Built full stack store"}]
    }, headers=headers)
    assert create_res.status_code == 200
    session_data = create_res.json()
    session_id = session_data["session_id"]
    total_q = session_data["total_questions"]
    assert total_q == 13

    # 3. Answer all 13 questions
    for i in range(total_q):
        payload = {
            "question_id": f"Q_{i+1}",
            "question_index": i,
            "transcript": f"This is my detailed technical answer for question {i+1} covering object oriented programming and system design.",
            "audio_duration": 30.0,
            "speaking_duration": 25.0,
            "wpm": 135.0,
            "filler_count": 1,
            "eye_contact_pct": 85.0,
            "face_status": "SINGLE_FACE"
        }
        if i >= 11:  # SQL questions
            payload["candidate_query"] = "SELECT * FROM Employees WHERE salary > 50000;"

        ans_res = client.post(f"/api/interview/{session_id}/answer", json=payload, headers=headers)
        assert ans_res.status_code == 200

    # 4. Complete Interview
    complete_res = client.post(f"/api/interview/{session_id}/complete", headers=headers)
    assert complete_res.status_code == 200
    complete_data = complete_res.json()
    assert complete_data["success"] is True
    assert "scores" in complete_data
    assert "feedback" in complete_data

    # 5. Fetch Results
    results_res = client.get(f"/api/interview/{session_id}/results", headers=headers)
    assert results_res.status_code == 200
    results_data = results_res.json()
    assert results_data["state"] == "FEEDBACK_READY"
    assert len(results_data["answers"]) == 13

    # 6. Download PDF
    pdf_res = client.get(f"/api/interview/{session_id}/pdf", headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"

