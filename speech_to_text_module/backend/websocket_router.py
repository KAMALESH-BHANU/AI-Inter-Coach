import json
import base64
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.speech_service import SpeechService
from app.services.vision_service import VisionService
from app.services.interview_service import load_session
from app.db.models import InterviewState
from app.config import settings
from app.utils.logger import logger

router = APIRouter(tags=["WebSocket Real-Time Feed"])

@router.websocket("/ws/interview/{session_id}")
async def websocket_interview_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info(f"WebSocket client connected for interview session {session_id}")

    # Reset vision observation window for fresh interview session
    VisionService.reset_window()

    live_transcript_parts = []
    total_audio_duration = 0.0
    total_speaking_duration = 0.0

    try:
        while True:
            data_str = await websocket.receive_text()

            # Check if session is completed on backend - stop processing if completed
            session = await load_session(session_id)
            if session and session.state in [InterviewState.COMPLETED, InterviewState.ANALYZING, InterviewState.FEEDBACK_READY]:
                logger.info(f"Session {session_id} is in state {session.state}. Stopping WebSocket processing.")
                await websocket.send_json({"type": "session_completed", "status": session.state.value})
                await websocket.close()
                break

            try:
                msg = json.loads(data_str)
                msg_type = msg.get("type")

                # 1. Process Video Frame
                if msg_type == "frame":
                    b64_img = msg.get("image", "")
                    vision_res = VisionService.analyze_frame_base64(b64_img)
                    
                    await websocket.send_json({
                        "type": "vision_update",
                        "timestamp": vision_res.get("timestamp"),
                        "face_count": vision_res.get("face_count", 0),
                        "face_status": vision_res.get("face_status", "FACE_MISSING"),
                        "face_detected": vision_res.get("face_detected", False),
                        "eye_contact_pct": vision_res.get("eye_contact_pct", -1.0),
                        "eye_contact": vision_res.get("eye_contact", False),
                        "head_pose": vision_res.get("head_pose", {"yaw": 0.0, "pitch": 0.0, "roll": 0.0}),
                        "gaze": vision_res.get("gaze", {"horizontal": 0.0, "vertical": 0.0}),
                        "expression": vision_res.get("expression", "Neutral"),
                        "warning": vision_res.get("warning")
                    })

                # 2. Process Audio Chunk
                elif msg_type == "audio":
                    b64_audio = msg.get("audio", "")
                    if b64_audio:
                        if "," in b64_audio:
                            b64_audio = b64_audio.split(",")[1]
                        audio_bytes = base64.b64decode(b64_audio)
                        
                        text_chunk, dur, speak_dur = SpeechService.transcribe_audio_bytes(audio_bytes)
                        if text_chunk:
                            live_transcript_parts.append(text_chunk)
                        total_audio_duration += dur
                        total_speaking_duration += speak_dur

                        full_transcript = " ".join(live_transcript_parts)
                        word_count = len(full_transcript.split())
                        
                        wpm = SpeechService.calculate_wpm(word_count, total_speaking_duration)
                        filler_res = SpeechService.analyze_filler_words(full_transcript, total_audio_duration)
                        pause_res = SpeechService.analyze_pauses(full_transcript, total_audio_duration, total_speaking_duration)

                        speaking_state = "SPEAKING" if (text_chunk or speak_dur > 0.5) else "SILENT"

                        await websocket.send_json({
                            "type": "speech_update",
                            "transcript": full_transcript,
                            "latest_chunk": text_chunk,
                            "speaking_state": speaking_state,
                            "wpm": wpm,
                            "word_count": word_count,
                            "filler_count": filler_res.get("total_fillers", 0),
                            "filler_rate": filler_res.get("filler_rate", 0.0),
                            "filler_words": filler_res.get("filler_words", {}),
                            "pause_count": pause_res.get("pause_count", 0),
                            "average_pause_sec": pause_res.get("average_pause_sec", 0.0),
                            "longest_pause_sec": pause_res.get("longest_pause_sec", 0.0)
                        })

            except Exception as e:
                logger.error(f"Error processing WebSocket message frame: {e}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"Unexpected WebSocket error for session {session_id}: {e}")
