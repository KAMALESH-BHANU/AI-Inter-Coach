from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class CommunicationFeedback(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    eyeContact: str = Field(..., alias='eyeContact', description='Feedback on eye contact and camera engagement')
    speakingPace: str = Field(..., alias='speakingPace', description='Feedback on words per minute and cadence')
    fillerWords: str = Field(..., alias='fillerWords', description='Feedback on filler words frequency and control')
    pauses: str = Field(..., alias='pauses', description='Feedback on pause duration and thinking intervals')
    clarity: str = Field(..., alias='clarity', description='Feedback on verbal articulation and message structure')

class TechnicalFeedbackItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    topic: str = Field(..., description='Technical domain or skill area')
    observation: str = Field(..., description='Specific observation from candidate answers')
    recommendation: str = Field(..., description='Concrete actionable recommendation to improve')

class QuestionWiseFeedback(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    questionNumber: int = Field(..., alias='questionNumber', description='1-based question number (1 to 13)')
    feedback: str = Field(..., description='Specific evaluation of candidate response')
    improvementSuggestion: str = Field(..., alias='improvementSuggestion', description='Direct coaching suggestion for this question')

class PracticePlanItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    day: int = Field(..., description='Plan day (1 to 5)')
    focus: str = Field(..., description='Primary learning/practice focus for the day')
    tasks: List[str] = Field(default_factory=list, description='Actionable daily practice tasks')

class GeminiSuggestionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    overallSummary: str = Field(..., alias='overallSummary', description='Comprehensive coaching summary')
    strengths: List[str] = Field(default_factory=list, max_length=5, description='Up to 5 top candidate strengths')
    improvementAreas: List[str] = Field(default_factory=list, max_length=5, alias='improvementAreas', description='Up to 5 top areas for growth')
    communicationFeedback: CommunicationFeedback = Field(..., alias='communicationFeedback', description='Detailed communication assessment')
    technicalFeedback: List[TechnicalFeedbackItem] = Field(default_factory=list, max_length=8, alias='technicalFeedback', description='Up to 8 technical domain reviews')
    questionWiseFeedback: List[QuestionWiseFeedback] = Field(default_factory=list, max_length=13, alias='questionWiseFeedback', description='Up to 13 question-specific coaching items')
    recommendedTopics: List[str] = Field(default_factory=list, max_length=8, alias='recommendedTopics', description='Up to 8 recommended topics to study')
    practicePlan: List[PracticePlanItem] = Field(default_factory=list, min_length=5, max_length=5, alias='practicePlan', description='Exactly 5-day structured practice plan')
    nextInterviewGoals: List[str] = Field(default_factory=list, max_length=5, alias='nextInterviewGoals', description='Up to 5 concrete goals for next mock interview')
    isFallback: bool = Field(default=False, alias='isFallback', description='Whether this response is a deterministic offline fallback')
    fallbackReason: Optional[str] = Field(default=None, alias='fallbackReason', description='Reason for fallback if applicable')
    generatedAt: Optional[datetime] = Field(default_factory=datetime.utcnow, alias='generatedAt', description='Generation timestamp')

# =========================================================================
# Input Payload Schemas (Strict Mapping Layer)
# =========================================================================

class CandidateProfilePayload(BaseModel):
    skills: List[str] = []
    projects: List[Dict[str, Any]] = []
    targetRole: str = 'Software Engineer'

class ScoreSummaryPayload(BaseModel):
    totalQuestions: int = 13
    answeredQuestions: int = 13
    overallScore: float = 0.0
    speechScore: float = 0.0
    technicalScore: float = 0.0
    pseudocodeScore: float = 0.0
    sqlScore: float = 0.0

class CommunicationMetricsPayload(BaseModel):
    eyeContactPercentage: float = 0.0
    wordsPerMinute: float = 0.0
    fillerWordCount: int = 0
    pauseCount: int = 0
    faceMissingEvents: int = 0
    multipleFaceEvents: int = 0
    faceStatusSummary: str = 'Normal'

class QuestionResultPayload(BaseModel):
    questionNumber: int
    questionType: str # INTRODUCTION | PROJECT | TECHNICAL | PSEUDOCODE_MCQ | SQL
    skill: Optional[str] = None
    topic: Optional[str] = None
    question: str
    candidateTranscript: Optional[str] = None # Q1-Q9 only
    selectedOption: Optional[str] = None # Q10-Q11 only
    candidateQuery: Optional[str] = None # Q12-Q13 only
    isCorrect: Optional[bool] = None # Q10-Q13
    score: float = 0.0
    maxScore: float = 100.0
    missingConcepts: List[str] = []
    evaluationNotes: str = ''

class InterviewAnalysisPayload(BaseModel):
    candidateProfile: CandidateProfilePayload
    scoreSummary: ScoreSummaryPayload
    communicationMetrics: CommunicationMetricsPayload
    questionResults: List[QuestionResultPayload]
