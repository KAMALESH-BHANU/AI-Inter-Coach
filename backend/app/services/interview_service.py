import uuid
from typing import List, Dict, Any, Optional
from app.db.models import InterviewSessionModel, InterviewState
from app.db.database import db
from app.services.question_service import QuestionService
from app.utils.logger import logger

MEMORY_SESSIONS: Dict[str, InterviewSessionModel] = {}

async def create_interview_session(user_id: str, candidate_skills: List[str], projects: List[Dict[str, Any]] = None) -> InterviewSessionModel:
    session_id = str(uuid.uuid4())
    questions = QuestionService.generate_interview_questions(candidate_skills, projects)
    
    session = InterviewSessionModel(
        id=session_id,
        user_id=user_id,
        state=InterviewState.READY,
        skills=candidate_skills,
        projects=projects or [],
        questions=questions,
        current_question_index=0
    )

    await save_session(session)
    return session

async def load_session(session_id: str) -> Optional[InterviewSessionModel]:
    if db.is_connected and db.db is not None:
        try:
            doc = await db.db.interviews.find_one({"id": session_id})
            if doc:
                return InterviewSessionModel(**doc)
        except Exception as e:
            logger.error(f"Error loading session {session_id} from MongoDB: {e}")

    return MEMORY_SESSIONS.get(session_id)

async def save_session(session: InterviewSessionModel) -> None:
    MEMORY_SESSIONS[session.id] = session
    if db.is_connected and db.db is not None:
        try:
            # Use mode="json" so Enums and Datetimes serialize to MongoDB primitive types
            doc = session.model_dump(mode="json")
            await db.db.interviews.update_one(
                {"id": session.id},
                {"$set": doc},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error saving session {session.id} to MongoDB: {e}")
