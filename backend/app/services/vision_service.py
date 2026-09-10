import cv2
import numpy as np
import base64
import math
import time
import os
from collections import deque
from typing import Dict, Any, List, Optional
from app.config import settings
from app.db.models import FaceStatus
from app.utils.logger import logger

class VisionService:
    _landmarker = None
    _haar_cascade = None
    _haar_alt2 = None
    _eye_cascade = None
    _detector_initialized = False

    # Rolling window of recent valid observations for temporal smoothing
    _observation_window: deque = deque(maxlen=settings.EYE_CONTACT_WINDOW_SIZE)

    @classmethod
    def initialize_detector(cls):
        if cls._detector_initialized:
            return

        # 1. Initialize Google MediaPipe Tasks FaceLandmarker (supports up to 5 faces)
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(base_dir, 'models', 'mediapipe', 'face_landmarker.task')

            if os.path.exists(model_path):
                base_options = python.BaseOptions(model_asset_path=model_path)
                options = vision.FaceLandmarkerOptions(
                    base_options=base_options,
                    output_face_blendshapes=True,
                    output_facial_transformation_matrixes=True,
                    num_faces=5,
                    min_face_detection_confidence=settings.FACE_DETECTION_CONFIDENCE,
                    min_face_presence_confidence=settings.FACE_DETECTION_CONFIDENCE,
                    min_tracking_confidence=settings.FACE_TRACKING_CONFIDENCE
                )
                cls._landmarker = vision.FaceLandmarker.create_from_options(options)
                logger.info("MediaPipe FaceLandmarker Tasks detector initialized (max 5 faces).")
            else:
                logger.warning(f"MediaPipe task model not found at {model_path}.")
                cls._landmarker = None
        except Exception as e:
            logger.warning(f"Could not initialize MediaPipe FaceLandmarker ({e}). Using OpenCV Cascade fallback.")
            cls._landmarker = None

        # 2. Initialize Local OpenCV Haar Cascades for fallback
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cascade_dir = os.path.join(base_dir, 'models', 'haarcascades')
            
            p_default = os.path.join(cascade_dir, 'haarcascade_frontalface_default.xml')
            p_alt2 = os.path.join(cascade_dir, 'haarcascade_frontalface_alt2.xml')
            p_eye = os.path.join(cascade_dir, 'haarcascade_eye.xml')

            if os.path.exists(p_default):
                cls._haar_cascade = cv2.CascadeClassifier(p_default)
            if os.path.exists(p_alt2):
                cls._haar_alt2 = cv2.CascadeClassifier(p_alt2)
            if os.path.exists(p_eye):
                cls._eye_cascade = cv2.CascadeClassifier(p_eye)
        except Exception as e:
            logger.error(f"Failed to load OpenCV Haar Cascade classifier: {e}")

        cls._detector_initialized = True

    @classmethod
    def reset_window(cls):
        cls._observation_window.clear()

    @classmethod
    def _empty_metrics(cls, reason: str = "") -> Dict[str, Any]:
        return cls._build_result(
            timestamp=time.time(),
            face_count=0,
            face_status=FaceStatus.FACE_MISSING,
            face_confidence=0.0,
            head_pose={"yaw": 0.0, "pitch": 0.0, "roll": 0.0},
            gaze={"horizontal": 0.0, "vertical": 0.0},
            eye_contact=False,
            eye_contact_pct=0.0,
            expression="Face Missing",
            warning=f"WARNING: Face Missing ({reason})" if reason else "WARNING: Face Missing"
        )

    @classmethod
    def analyze_frame_base64(cls, base64_image: str) -> Dict[str, Any]:
        """
        Processes a base64 encoded image frame and computes unified vision metrics.
        Returns single shared result containing explicit face_status, 3D head pose, gaze, and dynamic eye contact.
        """
        cls.initialize_detector()
        now_ts = time.time()

        try:
            if not base64_image:
                return cls._empty_metrics("Empty image frame")

            if "," in base64_image:
                base64_image = base64_image.split(",")[1]

            img_bytes = base64.b64decode(base64_image)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                return cls._empty_metrics("Decoding error")

            h, w, _ = img.shape
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            face_count = 0
            face_landmarks_list = []
            mediapipe_executed = False

            # 1. Primary: MediaPipe FaceLandmarker Detection
            if cls._landmarker:
                try:
                    import mediapipe as mp
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_img)
                    detection_result = cls._landmarker.detect(mp_image)
                    mediapipe_executed = True
                    if detection_result and detection_result.face_landmarks:
                        face_landmarks_list = detection_result.face_landmarks
                        face_count = len(face_landmarks_list)
                except Exception as e:
                    logger.debug(f"MediaPipe detection error: {e}")
                    mediapipe_executed = False

            # 2. Secondary Fallback: OpenCV Haar Cascade ONLY if MediaPipe was unavailable/failed
            if face_count == 0 and not mediapipe_executed:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                # Use standard gray with strict minNeighbors=6 to eliminate background false positives
                faces = ()
                if cls._haar_alt2 and not cls._haar_alt2.empty():
                    faces = cls._haar_alt2.detectMultiScale(
                        gray, scaleFactor=1.15, minNeighbors=6, minSize=(60, 60)
                    )
                if len(faces) == 0 and cls._haar_cascade and not cls._haar_cascade.empty():
                    faces = cls._haar_cascade.detectMultiScale(
                        gray, scaleFactor=1.15, minNeighbors=6, minSize=(60, 60)
                    )

                face_count = len(faces)

            # Determine explicit face status enum
            if face_count == 0:
                face_status = FaceStatus.FACE_MISSING
                warning = "WARNING: Face Missing"
            elif face_count == 1:
                face_status = FaceStatus.SINGLE_FACE
                warning = None
            else:
                face_status = FaceStatus.MULTIPLE_FACES
                warning = f"WARNING: Multiple Faces ({face_count}) Detected"

            # Compute detailed 3D Pose & Gaze if at least 1 face exists
            if face_count >= 1 and len(face_landmarks_list) > 0:
                landmarks = face_landmarks_list[0]
                head_pose, gaze, eye_contact_bool, conf, expression = cls._compute_pose_gaze_mp(landmarks, w, h)
            elif face_count >= 1:
                # Haar cascade fallback defaults
                head_pose = {"yaw": 0.0, "pitch": 0.0, "roll": 0.0}
                gaze = {"horizontal": 0.0, "vertical": 0.0}
                eye_contact_bool = True
                conf = 0.85
                expression = "Neutral"
            else:
                head_pose = {"yaw": 0.0, "pitch": 0.0, "roll": 0.0}
                gaze = {"horizontal": 0.0, "vertical": 0.0}
                eye_contact_bool = False
                conf = 0.0
                expression = "Face Missing"

            # Record observation into rolling window (only valid face frames add to observation history)
            if face_status != FaceStatus.FACE_MISSING:
                cls._observation_window.append({
                    "timestamp": now_ts,
                    "eye_contact": eye_contact_bool,
                    "confidence": conf
                })
            else:
                # If face is missing, record non-contact or decay
                cls._observation_window.append({
                    "timestamp": now_ts,
                    "eye_contact": False,
                    "confidence": 0.0
                })

            # Calculate temporal eye contact %
            if len(cls._observation_window) < 3:
                eye_contact_pct = -1.0  # Signals "Calculating..." to UI
            else:
                valid_looking = sum(1 for obs in cls._observation_window if obs["eye_contact"])
                eye_contact_pct = round((valid_looking / float(len(cls._observation_window))) * 100.0, 1)

            result = cls._build_result(
                timestamp=now_ts,
                face_count=face_count,
                face_status=face_status,
                face_confidence=conf,
                head_pose=head_pose,
                gaze=gaze,
                eye_contact=eye_contact_bool,
                eye_contact_pct=eye_contact_pct,
                expression=expression,
                warning=warning
            )

            if settings.DEBUG_MODE and face_count != 1:
                logger.info(f"[VISION] face_count={face_count} status={face_status.value} warning={warning}")

            return result

        except Exception as e:
            logger.error(f"Error analyzing vision frame: {e}")
            return cls._build_result(now_ts, 0, FaceStatus.FACE_MISSING, 0.0, {"yaw": 0.0, "pitch": 0.0, "roll": 0.0}, {"horizontal": 0.0, "vertical": 0.0}, False, 0.0, "Face Missing", f"WARNING: Face Missing ({str(e)})")

    @classmethod
    def _compute_pose_gaze_mp(cls, landmarks, width: int, height: int):
        """
        Calculates 3D Head Pose (yaw, pitch, roll) & Pupil Iris Gaze deviation using MediaPipe landmarks.
        """
        def get_pt(idx):
            lm = landmarks[idx]
            return np.array([lm.x * width, lm.y * height])

        nose = get_pt(1)
        chin = get_pt(152)
        left_eye_outer = get_pt(33)
        right_eye_outer = get_pt(263)

        eye_center = (left_eye_outer + right_eye_outer) / 2.0
        eye_dist = max(np.linalg.norm(left_eye_outer - right_eye_outer), 1.0)

        # Yaw (side-to-side rotation)
        nose_dx = (nose[0] - eye_center[0]) / eye_dist
        yaw_angle = math.degrees(math.atan(nose_dx * 1.5))

        # Pitch (up-down rotation)
        face_height = max(np.linalg.norm(chin - eye_center), 1.0)
        pitch_ratio = (nose[1] - eye_center[1]) / face_height
        pitch_angle = (pitch_ratio - 0.35) * 80.0

        # Roll (head tilt)
        eye_dy = right_eye_outer[1] - left_eye_outer[1]
        eye_dx = right_eye_outer[0] - left_eye_outer[0]
        roll_angle = math.degrees(math.atan2(eye_dy, eye_dx))

        # Gaze estimation using Refined Iris Landmarks (468 for left pupil, 473 for right pupil)
        gaze_h = 0.0
        gaze_v = 0.0
        try:
            if len(landmarks) > 473:
                left_pupil = get_pt(468)
                right_pupil = get_pt(473)
                left_eye_inner = get_pt(133)
                right_eye_inner = get_pt(362)

                left_ratio = np.linalg.norm(left_pupil - left_eye_outer) / max(np.linalg.norm(left_eye_inner - left_eye_outer), 1.0)
                right_ratio = np.linalg.norm(right_pupil - right_eye_inner) / max(np.linalg.norm(right_eye_outer - right_eye_inner), 1.0)
                gaze_h = round(float((left_ratio + right_ratio) / 2.0 - 0.5), 2)
        except Exception:
            gaze_h = 0.0

        # Check eye contact thresholds
        yaw_ok = abs(yaw_angle) <= settings.EYE_CONTACT_YAW_THRESHOLD
        pitch_ok = abs(pitch_angle) <= settings.EYE_CONTACT_PITCH_THRESHOLD
        gaze_ok = abs(gaze_h) <= settings.GAZE_HORIZONTAL_THRESHOLD

        eye_contact_bool = yaw_ok and pitch_ok and gaze_ok

        # Expression heuristic
        top_lip = get_pt(13)
        bot_lip = get_pt(14)
        mouth_opening = np.linalg.norm(top_lip - bot_lip) / eye_dist

        expression = "Speaking" if mouth_opening > 0.38 else "Neutral"

        head_pose = {
            "yaw": round(float(yaw_angle), 1),
            "pitch": round(float(pitch_angle), 1),
            "roll": round(float(roll_angle), 1)
        }
        gaze = {
            "horizontal": round(float(gaze_h), 2),
            "vertical": round(float(gaze_v), 2)
        }

        return head_pose, gaze, eye_contact_bool, 0.95, expression

    @staticmethod
    def _build_result(
        timestamp: float,
        face_count: int,
        face_status: FaceStatus,
        face_confidence: float,
        head_pose: Dict[str, float],
        gaze: Dict[str, float],
        eye_contact: bool,
        eye_contact_pct: float,
        expression: str,
        warning: Optional[str]
    ) -> Dict[str, Any]:
        return {
            "timestamp": timestamp,
            "face_count": face_count,
            "face_status": face_status.value,
            "face_detected": face_count > 0,
            "face_confidence": face_confidence,
            "head_pose": head_pose,
            "gaze": gaze,
            "eye_contact": eye_contact,
            "eye_contact_pct": eye_contact_pct,
            "expression": expression,
            "warning": warning
        }
