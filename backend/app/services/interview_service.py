import uuid
from typing import List, Dict, Any, Optional
from app.db.models import InterviewSessionModel, InterviewState
from app.db.database import db
from app.services.question_service import QuestionService
from app.utils.logger import logger

MEMORY_SESSIONS: Dict[str, InterviewSessionModel] = {}
MEMORY_USER_HISTORY: Dict[str, Dict[str, List[str]]] = {}

async def create_interview_session(user_id: str, candidate_skills: List[str], projects: List[Dict[str, Any]] = None) -> InterviewSessionModel:
    session_id = str(uuid.uuid4())
    recent_ids: List[str] = []
    recent_fps: List[str] = []

    # Fetch user history from MongoDB or memory
    if db.is_connected and db.db is not None:
        try:
            user_doc = await db.db.users.find_one({"id": user_id})
            if user_doc:
                recent_ids = user_doc.get("recent_technical_question_ids", [])
                recent_fps = user_doc.get("recent_technical_question_fingerprints", [])
        except Exception as e:
            logger.error(f"Error fetching user recent question history for {user_id}: {e}")
    else:
        user_hist = MEMORY_USER_HISTORY.get(user_id, {})
        recent_ids = user_hist.get("ids", [])
        recent_fps = user_hist.get("fingerprints", [])

    questions = QuestionService.generate_interview_questions(
        candidate_skills=candidate_skills,
        projects=projects,
        recent_question_ids=recent_ids,
        recent_question_fingerprints=recent_fps
    )

    # Collect newly selected technical question IDs and fingerprints
    new_tech_ids = [q.id for q in questions if q.type.value == "technical"]
    new_tech_fps = [QuestionService.create_question_fingerprint(q) if hasattr(QuestionService, "create_question_fingerprint") else q.id for q in questions if q.type.value == "technical"]

    # Update history bounded to last 50 entries
    updated_ids = (recent_ids + [qid for qid in new_tech_ids if qid not in recent_ids])[-50:]
    updated_fps = (recent_fps + [fp for fp in new_tech_fps if fp not in recent_fps])[-50:]

    MEMORY_USER_HISTORY[user_id] = {
        "ids": updated_ids,
        "fingerprints": updated_fps
    }

    if db.is_connected and db.db is not None:
        try:
            await db.db.users.update_one(
                {"id": user_id},
                {"$set": {
                    "recent_technical_question_ids": updated_ids,
                    "recent_technical_question_fingerprints": updated_fps
                }}
            )
        except Exception as e:
            logger.error(f"Error saving updated question history for user {user_id}: {e}")
    
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
