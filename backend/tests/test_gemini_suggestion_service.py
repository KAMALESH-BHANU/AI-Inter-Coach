import json
import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, MagicMock
from app.config import settings
from app.db.models import (
    InterviewSessionModel, QuestionModel, CandidateAnswerModel,
    QuestionType, ScoreBreakdown, SpeechMetricsSummary, VisionMetricsSummary,
    FaceMonitoringSummary, UserModel
)
from app.schemas.suggestion_schema import (
    GeminiSuggestionResponse, CommunicationFeedback, TechnicalFeedbackItem,
    PracticePlanItem, QuestionWiseFeedback
)
from app.services.gemini_suggestion_service import GeminiSuggestionService
from app.services.report_service import ReportService

@pytest.fixture
def sample_session():
    questions = [
        QuestionModel(
            id="INTRO_001",
            skill="Introduction",
            difficulty="easy",
            type=QuestionType.INTRODUCTION,
            question="Tell me about yourself.",
            expected_concepts=["Background", "Projects", "Goals"]
        ),
        QuestionModel(
            id="PROJ_001",
            skill="Project Architecture",
            difficulty="medium",
            type=QuestionType.PROJECT,
            question="Walk me through the architecture of your distributed cache.",
            expected_concepts=["Cache Invalidation", "Consistency", "Throughput"]
        ),
        QuestionModel(
            id="JAVA_001",
            skill="Java",
            difficulty="medium",
            type=QuestionType.TECHNICAL,
            question="Explain JVM garbage collection generations.",
            expected_concepts=["Young Gen", "Old Gen", "Eden", "Survivor", "G1"]
        ),
        QuestionModel(
            id="PSEUDO_001",
            skill="Logic & Algorithms",
            difficulty="medium",
            type=QuestionType.PSEUDOCODE_MCQ,
            question="What is the output of the loop?",
            options=[{"id": "A", "text": "10"}, {"id": "B", "text": "20"}, {"id": "C", "text": "30"}, {"id": "D", "text": "40"}],
            correctOptionId="B"
        ),
        QuestionModel(
            id="SQL_001",
            skill="MySQL Database",
            difficulty="medium",
            type=QuestionType.SQL,
            question="Find the top 3 highest paid employees.",
            expected_query="SELECT name, salary FROM Employees ORDER BY salary DESC LIMIT 3;",
            tables=[
                {"name": "Employees", "columns": ["id", "name", "email", "salary", "department_id"], "rows": [[1, "Alice", "a@test.com", 90000, 1]] * 5},
                {"name": "Departments", "columns": ["id", "dept_name", "building", "budget", "head"], "rows": [[1, "Engineering", "B1", 500000, "Alice"]] * 5}
            ]
        )
    ]

    answers = [
        CandidateAnswerModel(
            question_id="INTRO_001",
            question_index=0,
            transcript="I am a backend developer with 3 years of experience in Java and distributed microservices.",
            technical_score=85.0,
            eye_contact_pct=80.0,
            wpm=130.0,
            filler_count=2,
            pause_count=1
        ),
        CandidateAnswerModel(
            question_id="PROJ_001",
            question_index=1,
            transcript="Our cache layer uses Redis with write-through policy to maintain consistency with PostgreSQL.",
            technical_score=80.0,
            eye_contact_pct=75.0,
            wpm=135.0,
            filler_count=3,
            pause_count=2
        ),
        CandidateAnswerModel(
            question_id="JAVA_001",
            question_index=2,
            transcript="JVM divides heap into Young and Old generation. New objects are allocated in Eden space.",
            technical_score=90.0,
            eye_contact_pct=85.0,
            wpm=140.0,
            filler_count=1,
            pause_count=1
        ),
        CandidateAnswerModel(
            question_id="PSEUDO_001",
            question_index=3,
            selected_option_id="B",
            is_correct=True,
            technical_score=100.0,
            status="ANSWERED"
        ),
        CandidateAnswerModel(
            question_id="SQL_001",
            question_index=4,
            candidate_query="SELECT name, salary FROM Employees ORDER BY salary DESC LIMIT 3;",
            is_correct=True,
            technical_score=100.0,
            status="ANSWERED"
        )
    ]

    session = InterviewSessionModel(
        id="session-test-uuid-1234",
        user_id="user-test-uuid-5678",
        skills=["Java", "Spring Boot", "MySQL"],
        projects=[{"name": "Distributed Cache", "technologies": ["Java", "Redis"]}],
        questions=questions,
        answers=answers,
        scores=ScoreBreakdown(
            overall_score=88.0,
            technical_knowledge=85.0,
            communication=82.0,
            speech_fluency=85.0,
            pseudocode_score=100.0,
            sql_score=100.0,
            eye_contact=80.0
        ),
        speech_metrics=SpeechMetricsSummary(
            total_words=250,
            average_wpm=135.0,
            total_fillers=6
        ),
        vision_metrics=VisionMetricsSummary(
            average_eye_contact_pct=80.0,
            face_monitoring=FaceMonitoringSummary(
                single_face_percentage=98.0,
                missing_face_events=0,
                multiple_face_events=0
            )
        )
    )
    return session

def test_gemini_config_and_startup_validation():
    """Test 1: Config loading, timeout settings, and safe API key validation."""
    assert hasattr(settings, "GEMINI_TIMEOUT_SECONDS")
    assert hasattr(settings, "GEMINI_MAX_OUTPUT_TOKENS")
    assert hasattr(settings, "is_gemini_configured")

def test_compact_payload_construction_privacy(sample_session):
    """Test 2: Compact payload mapping isolates spoken vs MCQ vs SQL answers with zero sensitive data."""
    payload = GeminiSuggestionService.build_analysis_payload(sample_session)
    
    assert "candidateProfile" in payload
    assert "scoreSummary" in payload
    assert "communicationMetrics" in payload
    assert "questionResults" in payload

    # Check privacy: no passwords, tokens, full video paths, etc.
    payload_str = json.dumps(payload)
    assert "password" not in payload_str
    assert "token" not in payload_str
    assert "video_path" not in payload_str

    # Check question isolation
    q_res = payload["questionResults"]
    assert len(q_res) == 5

    # Q1-Q3: Spoken transcript present, candidateQuery is None, selectedOption is None
    for idx in range(3):
        assert q_res[idx]["candidateTranscript"] is not None
        assert q_res[idx]["selectedOption"] is None
        assert q_res[idx]["candidateQuery"] is None

    # Q4: Pseudocode MCQ -> selectedOption present, candidateTranscript is None
    assert q_res[3]["selectedOption"] == "B"
    assert q_res[3]["isCorrect"] is True
    assert q_res[3]["candidateTranscript"] is None
    assert q_res[3]["candidateQuery"] is None

    # Q5: SQL -> candidateQuery present, candidateTranscript is None, selectedOption is None
    assert "SELECT" in q_res[4]["candidateQuery"]
    assert q_res[4]["isCorrect"] is True
    assert q_res[4]["candidateTranscript"] is None
    assert q_res[4]["selectedOption"] is None

def test_gemini_suggestion_schema_validation():
    """Test 3: Pydantic schema validation on structured AI coaching output."""
    mock_llm_json = {
        "overallSummary": "Candidate performed well with strong Java concepts and optimal speaking pace.",
        "strengths": ["Clear articulation", "Strong JVM knowledge", "Accurate SQL query construction"],
        "improvementAreas": ["Explain cache invalidation trade-offs in deeper detail", "Practice silent pauses"],
        "communicationFeedback": {
            "eyeContact": "Maintained 80% camera gaze.",
            "speakingPace": "Speaking rate was 135 WPM, perfectly conversational.",
            "fillerWords": "Minimal filler words used.",
            "pauses": "Natural and well-timed pauses.",
            "clarity": "Structured answers clearly."
        },
        "technicalFeedback": [
            {
                "topic": "Java Memory Management",
                "observation": "Accurately described Eden and Survivor spaces.",
                "recommendation": "Review G1 garbage collector pause time goals."
            }
        ],
        "questionWiseFeedback": [
            {
                "questionNumber": 1,
                "feedback": "Strong concise elevator pitch.",
                "improvementSuggestion": "Keep highlighting key business metrics."
            }
        ],
        "recommendedTopics": ["JVM Tuning", "Redis Replication", "Advanced SQL"],
        "practicePlan": [
            {"day": 1, "focus": "Java Concurrency", "tasks": ["Review thread pools"]},
            {"day": 2, "focus": "System Design", "tasks": ["Design distributed cache"]},
            {"day": 3, "focus": "SQL Tuning", "tasks": ["Analyze query execution plans"]},
            {"day": 4, "focus": "Algorithm Tracing", "tasks": ["Trace recursion problems"]},
            {"day": 5, "focus": "Full Mock Interview", "tasks": ["Timed 13-question session"]}
        ],
        "nextInterviewGoals": ["Maintain >85% eye contact", "Ace all SQL challenges"]
    }

    model = GeminiSuggestionResponse.model_validate(mock_llm_json)
    assert model.overallSummary.startswith("Candidate performed well")
    assert len(model.strengths) == 3
    assert len(model.practicePlan) == 5
    assert model.communicationFeedback.speakingPace.startswith("Speaking rate was 135 WPM")

def test_deterministic_fallback_when_api_fails(sample_session):
    """Test 4: Deterministic fallback generates complete coaching plan when Gemini is unreachable."""
    payload = GeminiSuggestionService.build_analysis_payload(sample_session)
    fallback = GeminiSuggestionService.generate_deterministic_fallback(payload, fallback_reason="API Key Missing")

    assert fallback.isFallback is True
    assert fallback.fallbackReason == "API Key Missing"
    assert len(fallback.strengths) > 0
    assert len(fallback.improvementAreas) > 0
    assert len(fallback.practicePlan) == 5
    assert fallback.communicationFeedback.eyeContact != ""

def test_output_length_constraints_enforcement(sample_session):
    """Test 5: Arrays exceeding max lengths are safely clamped."""
    payload = GeminiSuggestionService.build_analysis_payload(sample_session)

    # Mock response with > 5 strengths and > 8 topics
    mock_overloaded_json = {
        "overallSummary": "Summary",
        "strengths": ["S1", "S2", "S3", "S4", "S5", "S6", "S7"],
        "improvementAreas": ["I1", "I2", "I3", "I4", "I5", "I6"],
        "communicationFeedback": {
            "eyeContact": "Good",
            "speakingPace": "Good",
            "fillerWords": "Good",
            "pauses": "Good",
            "clarity": "Good"
        },
        "technicalFeedback": [{"topic": f"T{i}", "observation": "Obs", "recommendation": "Rec"} for i in range(12)],
        "questionWiseFeedback": [{"questionNumber": i, "feedback": "Fb", "improvementSuggestion": "Sug"} for i in range(15)],
        "recommendedTopics": [f"Top{i}" for i in range(10)],
        "practicePlan": [{"day": i, "focus": f"Focus {i}", "tasks": ["Task"]} for i in range(1, 6)],
        "nextInterviewGoals": ["G1", "G2", "G3", "G4", "G5", "G6"]
    }

    mock_resp = MagicMock()
    mock_resp.text = f"```json\n{json.dumps(mock_overloaded_json)}\n```"

    with patch.object(settings, "GEMINI_API_KEY", "mock-test-key-12345"), \
         patch("google.genai.Client") as MockClient:
        client_instance = MockClient.return_value
        client_instance.models.generate_content.return_value = mock_resp

        res = asyncio.run(GeminiSuggestionService.generate_interview_suggestions(payload))

        assert res.isFallback is False
        assert len(res.strengths) <= 5
        assert len(res.improvementAreas) <= 5
        assert len(res.technicalFeedback) <= 8
        assert len(res.questionWiseFeedback) <= 13
        assert len(res.recommendedTopics) <= 8
        assert len(res.practicePlan) == 5
        assert len(res.nextInterviewGoals) <= 5

def test_pdf_generation_with_new_suggestions(sample_session):
    """Test 6: PDF report renders structured AI suggestions cleanly without errors."""
    payload = GeminiSuggestionService.build_analysis_payload(sample_session)
    sample_session.suggestions = GeminiSuggestionService.generate_deterministic_fallback(payload).model_dump(by_alias=True)

    pdf_bytes = ReportService.generate_pdf_report(sample_session, user_name="Alice Developer")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF")

from fastapi.testclient import TestClient
from app.main import app
from app.api.auth import get_current_user
from app.services.interview_service import save_session

def test_suggestions_api_endpoints_and_caching(sample_session):
    """Test 7: POST/GET suggestions endpoints, caching behavior, and duplicate request prevention."""
    user = UserModel(
        id=sample_session.user_id,
        email="alice@test.com",
        full_name="Alice Developer",
        hashed_password="hashed_pw_test"
    )

    app.dependency_overrides[get_current_user] = lambda: user
    client = TestClient(app)

    asyncio.run(save_session(sample_session))

    with patch.object(settings, "GEMINI_API_KEY", ""):
        # 1. First POST request generates suggestions and stores them
        resp = client.post(f"/api/interview/{sample_session.id}/suggestions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == sample_session.id
        assert data["cached"] is False
        assert "suggestions" in data
        assert data["suggestions"]["overallSummary"] != ""

        # 2. Second POST request returns cached suggestions without regenerating
        # Mark status as COMPLETED to verify caching
        sample_session.suggestion_status = "COMPLETED"
        asyncio.run(save_session(sample_session))

        resp2 = client.post(f"/api/interview/{sample_session.id}/suggestions")
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["cached"] is True

        # 3. GET request retrieves current suggestions
        resp3 = client.get(f"/api/interview/{sample_session.id}/suggestions")
        assert resp3.status_code == 200
        data3 = resp3.json()
        assert data3["session_id"] == sample_session.id
        assert data3["suggestions"] is not None

    app.dependency_overrides.clear()

def test_suggestions_authorization_security(sample_session):
    """Test 8: Unauthorized candidate cannot fetch or generate suggestions for another user's session."""
    attacker_user = UserModel(
        id="attacker-user-id-9999",
        email="attacker@test.com",
        full_name="Attacker",
        hashed_password="hashed_pw_test"
    )

    app.dependency_overrides[get_current_user] = lambda: attacker_user
    client = TestClient(app)

    asyncio.run(save_session(sample_session))

    # Attempt to generate suggestions for sample_session (belongs to user-test-uuid-5678)
    resp = client.post(f"/api/interview/{sample_session.id}/suggestions")
    assert resp.status_code == 403
    assert "Unauthorized" in resp.json()["detail"]

    # Attempt to get suggestions for sample_session
    resp_get = client.get(f"/api/interview/{sample_session.id}/suggestions")
    assert resp_get.status_code == 403
    assert "Unauthorized" in resp_get.json()["detail"]

    app.dependency_overrides.clear()
