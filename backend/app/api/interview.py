import os
import uuid
import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, status
from fastapi.responses import FileResponse
from app.db.models import (
    InterviewSessionModel, CandidateAnswerModel, InterviewState,
    UserModel, QuestionModel, SpeechMetricsSummary, VisionMetricsSummary,
    FaceMonitoringSummary, ScoreBreakdown
)
from app.db.database import db, get_db
from app.api.auth import get_current_user
from app.services.interview_service import create_interview_session, load_session, save_session, MEMORY_SESSIONS
from app.services.question_service import QuestionService
from app.services.scoring_service import ScoringService
from app.services.gemini_service import GeminiService
from app.services.report_service import ReportService
from app.services.cleanup_service import CleanupService
from app.utils.logger import logger

router = APIRouter(prefix="/api/interview", tags=["Interview Lifecycle"])

@router.post("/start", response_model=Dict[str, Any])
@router.post("/create", response_model=Dict[str, Any])
async def start_interview(
    payload: Dict[str, Any],
    current_user: UserModel = Depends(get_current_user)
):
    skills = payload.get("skills", [])
    projects = payload.get("projects", [])

    if not skills:
        skills = current_user.skills or ["Java", "Python"]

    try:
        session = await create_interview_session(
            user_id=current_user.id,
            candidate_skills=skills,
            projects=projects
        )
        return {
            "session_id": session.id,
            "state": session.state,
            "total_questions": len(session.questions),
            "current_question_index": 0,
            "current_question": session.questions[0] if session.questions else None,
            "questions": session.questions
        }
    except Exception as e:
        logger.error(f"Failed to start interview session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create interview session: {str(e)}")

@router.get("/{session_id}", response_model=Dict[str, Any])
async def get_interview_session(
    session_id: str,
    current_user: UserModel = Depends(get_current_user)
):
    session = await load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    current_q = None
    if session.questions and 0 <= session.current_question_index < len(session.questions):
        current_q = session.questions[session.current_question_index]

    return {
        "session_id": session.id,
        "state": session.state,
        "current_question_index": session.current_question_index,
        "total_questions": len(session.questions),
        "current_question": current_q,
        "questions": session.questions,
        "skills": session.skills,
        "answers_submitted": len(session.answers)
    }

@router.post("/{session_id}/answer")
async def submit_question_answer(
    session_id: str,
    payload: Dict[str, Any],
    current_user: UserModel = Depends(get_current_user)
):
    session = await load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    question_id = payload.get("question_id")
    question_index = payload.get("question_index", session.current_question_index)
    transcript = (payload.get("transcript") or "").strip()
    audio_duration = payload.get("audio_duration", 0.0)
    speaking_duration = payload.get("speaking_duration", audio_duration)
    wpm = payload.get("wpm", 0.0)
    filler_count = payload.get("filler_count", 0)
    filler_words = payload.get("filler_words", {})
    filler_rate = payload.get("filler_rate", 0.0)
    pause_count = payload.get("pause_count", 0)
    average_pause_sec = payload.get("average_pause_sec", 0.0)
    longest_pause_sec = payload.get("longest_pause_sec", 0.0)
    eye_contact_pct = payload.get("eye_contact_pct", 0.0)
    face_status = payload.get("face_status", "SINGLE_FACE")
    face_visibility_pct = payload.get("face_visibility_pct", 100.0)
    
    single_face_frames = payload.get("single_face_frames", 0)
    missing_face_frames = payload.get("missing_face_frames", 0)
    multiple_face_frames = payload.get("multiple_face_frames", 0)
    missing_face_events = payload.get("missing_face_events", 0)
    multiple_face_events = payload.get("multiple_face_events", 0)

    dominant_expression = payload.get("dominant_expression", "Neutral")
    selected_option = payload.get("selected_option")

    # Find target question model
    target_q = next((q for q in session.questions if q.id == question_id), None)
    if not target_q and 0 <= question_index < len(session.questions):
        target_q = session.questions[question_index]

    # Evaluate answer score independently (strictly 0 if unanswered)
    scores_res = ScoringService.evaluate_answer(
        question=target_q,
        answer_transcript=transcript,
        selected_option=selected_option,
        audio_duration=audio_duration,
        wpm=wpm,
        filler_count=filler_count,
        pause_count=pause_count,
        eye_contact_pct=eye_contact_pct
    )

    answer_model = CandidateAnswerModel(
        question_id=question_id or (target_q.id if target_q else "Q"),
        question_index=question_index,
        transcript=transcript,
        audio_duration=audio_duration,
        speaking_duration=speaking_duration,
        wpm=wpm,
        filler_count=filler_count,
        filler_words=filler_words,
        filler_rate=filler_rate,
        pause_count=pause_count,
        average_pause_sec=average_pause_sec,
        longest_pause_sec=longest_pause_sec,
        eye_contact_pct=eye_contact_pct,
        face_status=face_status,
        face_visibility_pct=face_visibility_pct,
        single_face_frames=single_face_frames,
        missing_face_frames=missing_face_frames,
        multiple_face_frames=multiple_face_frames,
        missing_face_events=missing_face_events,
        multiple_face_events=multiple_face_events,
        dominant_expression=dominant_expression,
        selected_option=selected_option,
        technical_score=scores_res.get("technical_score", 0.0),
        quality_score=scores_res.get("quality_score", 0.0),
        communication_score=scores_res.get("communication_score", 0.0),
        evaluated_at=datetime.datetime.utcnow()
    )

    # Save to atomic question list
    existing_idx = next((i for i, a in enumerate(session.answers) if a.question_index == question_index), -1)
    if existing_idx >= 0:
        session.answers[existing_idx] = answer_model
    else:
        session.answers.append(answer_model)

    # Advance current question index
    if session.current_question_index < len(session.questions) - 1:
        session.current_question_index += 1
        session.state = InterviewState.QUESTION_ACTIVE

    await save_session(session)

    current_next_q = None
    if session.questions and 0 <= session.current_question_index < len(session.questions):
        current_next_q = session.questions[session.current_question_index]

    return {
        "success": True,
        "saved_question_index": question_index,
        "next_question_index": session.current_question_index,
        "current_question": current_next_q,
        "questions": session.questions,
        "is_last_question": session.current_question_index >= len(session.questions)
    }

@router.post("/{session_id}/complete")
async def complete_interview(
    session_id: str,
    current_user: UserModel = Depends(get_current_user)
):
    session = await load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    session.state = InterviewState.ANALYZING
    await save_session(session)

    try:
        # Calculate final overall scores across all 10 questions
        scores = ScoringService.calculate_session_scores(session.questions, session.answers)
        session.scores = scores

        # Calculate speech & vision metrics summary
        valid_spoken_answers = [a for a in session.answers if a.transcript and len(a.transcript.strip()) >= 5]
        total_words = sum(len(a.transcript.split()) for a in session.answers)
        total_duration = sum(a.audio_duration for a in session.answers)
        total_speaking = sum(a.speaking_duration for a in session.answers)
        total_fillers = sum(a.filler_count for a in session.answers)
        
        avg_wpm = round(sum(a.wpm for a in valid_spoken_answers) / len(valid_spoken_answers), 1) if valid_spoken_answers else 0.0

        session.speech_metrics = SpeechMetricsSummary(
            total_words=total_words,
            total_duration_sec=total_duration,
            total_speaking_duration_sec=total_speaking,
            average_wpm=avg_wpm,
            total_fillers=total_fillers,
            fillers_per_minute=round(total_fillers / max(total_duration / 60.0, 0.1), 2) if total_duration > 0 else 0.0,
            average_pause_sec=round(sum(a.average_pause_sec for a in session.answers) / max(len(session.answers), 1), 2)
        )

        valid_eye_answers = [a.eye_contact_pct for a in session.answers if a.eye_contact_pct >= 0]
        avg_eye = round(sum(valid_eye_answers) / max(len(valid_eye_answers), 1), 1) if valid_eye_answers else 0.0

        # Calculate Face Proctoring Summary across all frame counts & events
        total_single_frames = sum(a.single_face_frames for a in session.answers)
        total_missing_frames = sum(a.missing_face_frames for a in session.answers)
        total_multiple_frames = sum(a.multiple_face_frames for a in session.answers)
        total_frames = total_single_frames + total_missing_frames + total_multiple_frames

        total_missing_events = sum(a.missing_face_events for a in session.answers)
        total_multiple_events = sum(a.multiple_face_events for a in session.answers)

        if total_frames > 0:
            single_face_pct = round((total_single_frames / total_frames) * 100.0, 1)
            missing_face_pct = round((total_missing_frames / total_frames) * 100.0, 1)
            multiple_face_pct = round((total_multiple_frames / total_frames) * 100.0, 1)
        else:
            single_face_pct = 100.0
            missing_face_pct = 0.0
            multiple_face_pct = 0.0

        face_monitoring = FaceMonitoringSummary(
            single_face_percentage=single_face_pct,
            missing_face_percentage=missing_face_pct,
            multiple_face_percentage=multiple_face_pct,
            multiple_face_events=total_multiple_events,
            missing_face_events=total_missing_events
        )

        session.vision_metrics = VisionMetricsSummary(
            average_eye_contact_pct=avg_eye,
            average_face_visibility_pct=round(100.0 - missing_face_pct, 1),
            head_pose_stability_pct=88.0,
            face_monitoring=face_monitoring
        )

        session.scores.eye_contact = avg_eye

        # Generate Gemini Feedback (or fallback)
        feedback = await GeminiService.generate_feedback(
            skills=session.skills,
            questions=session.questions,
            answers=session.answers,
            scores=session.scores
        )
        session.gemini_feedback = feedback
        session.state = InterviewState.FEEDBACK_READY
        await save_session(session)

        return {
            "success": True,
            "state": session.state,
            "scores": session.scores,
            "feedback": session.gemini_feedback
        }
    except Exception as e:
        logger.error(f"Error completing interview session {session_id}: {e}")
        session.state = InterviewState.FAILED
        session.error_message = str(e)
        await save_session(session)
        raise HTTPException(status_code=500, detail=f"Error finalizing interview: {str(e)}")

@router.post("/{session_id}/upload-video")
async def upload_interview_video(
    session_id: str,
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user)
):
    session = await load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    video_path = CleanupService.get_video_path(session_id)
    with open(video_path, "wb") as f:
        content = await file.read()
        f.write(content)

    session.video_path = video_path
    session.video_deleted = False
    await save_session(session)
    logger.info(f"Uploaded interview recording video for session {session_id} to {video_path}")
    return {"success": True, "message": "Video recording saved successfully"}

@router.get("/{session_id}/video")
async def get_interview_video(
    session_id: str,
    current_user: UserModel = Depends(get_current_user)
):
    session = await load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    video_path = CleanupService.get_video_path(session_id)
    if not os.path.exists(video_path) or session.video_deleted or session.video_replay_count >= 1:
        raise HTTPException(status_code=404, detail="Temporary interview video recording has expired or has already been viewed.")

    return FileResponse(video_path, media_type="video/webm")

@router.post("/{session_id}/delete-video")
async def delete_interview_video(
    session_id: str,
    current_user: UserModel = Depends(get_current_user)
):
    session = await load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    CleanupService.delete_video_file(session_id)
    session.video_deleted = True
    session.video_replay_count += 1
    await save_session(session)
    logger.info(f"Permanently purged temporary interview recording for session {session_id}")
    return {"success": True, "message": "Interview video deleted permanently"}

@router.get("/{session_id}/results")
async def get_interview_results(
    session_id: str,
    current_user: UserModel = Depends(get_current_user)
):
    session = await load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    video_path = CleanupService.get_video_path(session_id)
    has_video = os.path.exists(video_path) or not session.video_deleted

    return {
        "session_id": session.id,
        "state": session.state,
        "date": session.created_at,
        "skills": session.skills,
        "scores": session.scores,
        "speech_metrics": session.speech_metrics,
        "vision_metrics": session.vision_metrics,
        "gemini_feedback": session.gemini_feedback,
        "questions": session.questions,
        "answers": session.answers,
        "video_available": has_video and session.video_replay_count == 0
    }

@router.get("/{session_id}/pdf")
async def download_pdf_report(
    session_id: str,
    current_user: UserModel = Depends(get_current_user)
):
    session = await load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    pdf_bytes = ReportService.generate_pdf_report(session, current_user.full_name)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="AI_Interview_Report_{session_id[:8]}.pdf"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

@router.get("/history/user")
async def get_user_interview_history(current_user: UserModel = Depends(get_current_user)):
    user_sessions = []
    if db.is_connected and db.db is not None:
        cursor = db.db.interviews.find({"user_id": current_user.id}).sort("created_at", -1)
        async for doc in cursor:
            user_sessions.append(InterviewSessionModel(**doc))
    else:
        user_sessions = [s for s in MEMORY_SESSIONS.values() if s.user_id == current_user.id]

    history_list = []
    for s in user_sessions:
        history_list.append({
            "session_id": s.id,
            "date": s.created_at,
            "skills": s.skills,
            "state": s.state,
            "overall_score": s.scores.overall_score if s.scores else 0.0,
            "technical_score": s.scores.technical_knowledge if s.scores else 0.0,
            "communication_score": s.scores.communication if s.scores else 0.0
        })

    return history_list
