import pytest
import numpy as np
import cv2
import base64
from app.services.vision_service import VisionService

def create_synthetic_frame():
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.circle(img, (100, 100), 50, (255, 255, 255), -1)
    _, buffer = cv2.imencode('.jpg', img)
    return base64.b64encode(buffer).decode('utf-8')

def test_empty_metrics():
    metrics = VisionService._empty_metrics("Test reason")
    assert not metrics["face_detected"]
    assert metrics["face_status"] == "FACE_MISSING"
    assert metrics["eye_contact_pct"] == 0.0

def test_analyze_frame_synthetic():
    b64_str = create_synthetic_frame()
    metrics = VisionService.analyze_frame_base64(b64_str)
    assert "face_detected" in metrics
    assert "face_status" in metrics
    assert "eye_contact_pct" in metrics
    assert "expression" in metrics
