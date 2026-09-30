import uuid
import json
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, model_validator

class QuestionType(str, Enum):
    INTRODUCTION = "introduction"
    PROJECT = "project"
    TECHNICAL = "technical"
    PSEUDOCODE = "pseudocode"
    PSEUDOCODE_MCQ = "pseudocode_mcq"
    SQL = "sql"

class InterviewState(str, Enum):
    CREATED = "CREATED"
    READY = "READY"
    QUESTION_ACTIVE = "QUESTION_ACTIVE"
    ANSWERING = "ANSWERING"
    QUESTION_COMPLETED = "QUESTION_COMPLETED"
    COMPLETED = "COMPLETED"
    ANALYZING = "ANALYZING"
    FEEDBACK_READY = "FEEDBACK_READY"
    FAILED = "FAILED"

class FaceStatus(str, Enum):
    FACE_MISSING = "FACE_MISSING"
    SINGLE_FACE = "SINGLE_FACE"
    MULTIPLE_FACES = "MULTIPLE_FACES"

class QuestionModel(BaseModel):
    id: str
    skill: str
    difficulty: str  # easy, medium, hard
    type: QuestionType
    question: str
    expected_concepts: List[str] = []
    ideal_answer: str = ""
    explanation: Optional[str] = None
    code_snippet: Optional[str] = None
    options: Optional[List[Any]] = None  # for pseudocode MCQs (list of dicts [{"id": "A", "text": "..."}] or strings)
    correct_answer: Optional[str] = None
    correct_option_id: Optional[str] = None
    correctOptionId: Optional[str] = None
    # Technical and question family metadata
    concept: Optional[str] = None
    question_family: Optional[str] = None
    questionFamily: Optional[str] = None
    tags: Optional[List[str]] = []
    idealAnswer: Optional[str] = None
    # Pseudocode and general problem solving fields
    category: Optional[str] = None
    topic: Optional[str] = None
    prompt: Optional[str] = None
    input_description: Optional[str] = None
    input: Optional[str] = None
    expected_output_description: Optional[str] = None
    example: Optional[Dict[str, Any]] = None
    pseudocode: Optional[str] = None
    language_independent: Optional[bool] = True
    languageIndependent: Optional[bool] = True
    supported_languages: Optional[List[str]] = None
    answer_mode: Optional[str] = None
    answerMode: Optional[str] = None
    question_number: Optional[int] = None
    questionNumber: Optional[int] = None
    question_type: Optional[str] = None
    questionType: Optional[str] = None
    score: Optional[int] = 1
    # SQL specific fields
    title: Optional[str] = None
    description: Optional[str] = None
    tables: Optional[List[Dict[str, Any]]] = None
    expected_query: Optional[str] = None
    expected_output: Optional[Dict[str, Any]] = None
    expected_result: Optional[List[Dict[str, Any]]] = None

class CandidateAnswerModel(BaseModel):
    question_id: str
    question_index: int
    transcript: str = ""
    audio_duration: float = 0.0
    speaking_duration: float = 0.0
    wpm: float = 0.0
    filler_count: int = 0
    filler_words: Dict[str, int] = {}
    filler_rate: float = 0.0
    pause_count: int = 0
    average_pause_sec: float = 0.0
    longest_pause_sec: float = 0.0
    eye_contact_pct: float = 0.0
    face_status: FaceStatus = FaceStatus.SINGLE_FACE
    face_visibility_pct: float = 0.0
    single_face_frames: int = 0
    missing_face_frames: int = 0
    multiple_face_frames: int = 0
    missing_face_events: int = 0
    multiple_face_events: int = 0
    dominant_expression: str = "Neutral"
    # Pseudocode MCQ answer fields
    selected_option: Optional[str] = None
    selected_option_id: Optional[str] = None
    selectedOptionId: Optional[str] = None
    selected_option_text: Optional[str] = None
    selectedOptionText: Optional[str] = None
    correct_option_id: Optional[str] = None
    correctOptionId: Optional[str] = None
    answer_mode: Optional[str] = None
    answerMode: Optional[str] = None
    status: Optional[str] = None  # "ANSWERED" | "NOT_ANSWERED"
    # SQL specific answer fields
    candidate_query: Optional[str] = None
    query_result: Optional[List[Dict[str, Any]]] = None
    expected_result: Optional[List[Dict[str, Any]]] = None
    is_correct: Optional[bool] = None
    execution_error: Optional[str] = None
    execution_time_ms: Optional[float] = None
    technical_score: float = 0.0
    quality_score: float = 0.0
    communication_score: float = 0.0
    evaluated_at: Optional[datetime] = None

class SpeechMetricsSummary(BaseModel):
    total_words: int = 0
    total_duration_sec: float = 0.0
    total_speaking_duration_sec: float = 0.0
    average_wpm: float = 0.0
    total_fillers: int = 0
    fillers_per_minute: float = 0.0
    filler_breakdown: Dict[str, int] = {}
    average_pause_sec: float = 0.0

class FaceMonitoringSummary(BaseModel):
    single_face_percentage: float = 100.0
    missing_face_percentage: float = 0.0
    multiple_face_percentage: float = 0.0
    multiple_face_events: int = 0
    missing_face_events: int = 0

class VisionMetricsSummary(BaseModel):
    average_eye_contact_pct: float = 0.0
    average_face_visibility_pct: float = 0.0
    head_pose_stability_pct: float = 0.0
    expression_breakdown: Dict[str, float] = {}
    face_monitoring: FaceMonitoringSummary = Field(default_factory=FaceMonitoringSummary)

class ScoreBreakdown(BaseModel):
    technical_knowledge: float = 0.0
    answer_quality: float = 0.0
    communication: float = 0.0
    project_understanding: float = 0.0
    presentation: float = 0.0
    eye_contact: float = 0.0
    speech_fluency: float = 0.0
    pseudocode_score: float = 0.0
    sql_score: float = 0.0
    overall_score: float = 0.0

class GeminiFeedbackModel(BaseModel):
    overall_summary: str = ""
    strengths: List[str] = []
    areas_to_improve: List[str] = []
    technical_strengths: List[str] = []
    communication_strengths: List[str] = []
    technical_improvements: List[str] = []
    communication_improvements: List[str] = []
    project_feedback: List[str] = []
    specific_suggestions: List[str] = []
    recommended_topics: List[str] = []
    interview_readiness: str = "Needs Practice"
    final_feedback: str = ""
    is_fallback: bool = False

class InterviewSessionModel(BaseModel):
    id: str
    user_id: str
    state: InterviewState = InterviewState.CREATED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    skills: List[str] = []
    projects: List[Dict[str, Any]] = []
    resume_extracted: bool = False
    
    current_question_index: int = 0  # 0 to 12
    questions: List[QuestionModel] = []
    answers: List[CandidateAnswerModel] = []
    sql_question_ids: List[str] = []
    
    speech_metrics: SpeechMetricsSummary = Field(default_factory=SpeechMetricsSummary)
    vision_metrics: VisionMetricsSummary = Field(default_factory=VisionMetricsSummary)
    scores: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    gemini_feedback: Optional[GeminiFeedbackModel] = None
    
    # AI Suggestions & Feedback Service fields
    suggestions: Optional[Dict[str, Any]] = None
    suggestion_status: str = "NOT_REQUESTED"  # NOT_REQUESTED | GENERATING | COMPLETED | FAILED
    suggestion_attempts: int = 0
    suggestion_error: Optional[str] = None
    suggestions_generated_at: Optional[datetime] = None
    
    video_path: Optional[str] = None
    video_replay_count: int = 0
    video_deleted: bool = False
    error_message: Optional[str] = None

class UserModel(BaseModel):
    id: str
    email: str
    full_name: str = "Candidate"
    hashed_password: str
    skills: List[str] = []
    recent_technical_question_ids: List[str] = []
    recent_technical_question_fingerprints: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="before")
    @classmethod
    def normalize_user_dict(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # 1. Normalize ID
            if "id" not in data and "_id" in data:
                data["id"] = str(data["_id"])
            elif "id" in data and not data["id"]:
                data["id"] = str(data.get("_id", uuid.uuid4()))
            elif "id" not in data:
                data["id"] = str(uuid.uuid4())
            
            # 2. Normalize full_name
            if "full_name" not in data or not data["full_name"]:
                data["full_name"] = data.get("name") or data.get("username") or (data.get("email", "Candidate").split("@")[0])
            
            # 3. Normalize hashed_password
            if "hashed_password" not in data or not data["hashed_password"]:
                data["hashed_password"] = data.get("password_hash") or data.get("password") or ""
            
            # 4. Normalize skills
            skills_val = data.get("skills", [])
            if isinstance(skills_val, str):
                try:
                    data["skills"] = json.loads(skills_val)
                except Exception:
                    data["skills"] = [s.strip() for s in skills_val.split(",") if s.strip()]
            elif not isinstance(skills_val, list):
                data["skills"] = []
        return data
