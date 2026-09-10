import pytest
import numpy as np
import base64
import cv2
from app.services.vision_service import VisionService
from app.db.models import FaceStatus

def create_dummy_base64_frame(color=(128, 128, 128)):
    img = np.full((240, 320, 3), color, dtype=np.uint8)
    _, buffer = cv2.imencode('.jpg', img)
    return base64.b64encode(buffer).decode('utf-8')

def test_face_missing_on_blank_frame():
    VisionService.reset_window()
    b64_frame = create_dummy_base64_frame()
    result = VisionService.analyze_frame_base64(b64_frame)

    assert result["face_count"] == 0
    assert result["face_status"] == FaceStatus.FACE_MISSING.value
    assert result["face_detected"] is False
    assert result["warning"] is not None
    assert "WARNING" in result["warning"]

def test_result_structure():
    VisionService.reset_window()
    b64_frame = create_dummy_base64_frame()
    result = VisionService.analyze_frame_base64(b64_frame)

    assert "timestamp" in result
    assert "face_count" in result
    assert "face_status" in result
    assert "head_pose" in result
    assert "gaze" in result
    assert "eye_contact" in result
    assert "eye_contact_pct" in result
