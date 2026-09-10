# System Architecture — AI Interview Coach Platform

## Overview
The AI Interview Coach application is a production-style, modular platform designed for end-to-end real-time technical mock interviews on Windows 11 CPU hardware.

## System Topology
```
                  ┌─────────────────────────────────────────┐
                  │            React 18 Frontend            │
                  │   Vite + Tailwind CSS + Lucide Icons    │
                  └────────────────────┬────────────────────┘
                                       │
                         REST API & WebSockets (JSON/Binary)
                                       │
                  ┌────────────────────▼────────────────────┐
                  │             FastAPI Backend             │
                  └──────┬─────────────┬─────────────┬──────┘
                         │             │             │
        ┌────────────────┴┐    ┌───────┴──────┐    ┌─┴───────────────┐
        │  Speech Module  │    │Vision Module │    │ Question Engine │
        │  faster-whisper │    │ MediaPipe CV │    │ 10-Q Validator  │
        └─────────────────┘    └──────────────┘    └─────────────────┘
                         │             │             │
                  ┌──────▼─────────────▼─────────────▼──────┐
                  │        Scoring & Gemini LLM Engine       │
                  └────────────────────┬────────────────────┘
                                       │
                         ┌─────────────┴─────────────┐
                         │  MongoDB / PDF / Video    │
                         │    Auto-Cleanup TTL       │
                         └───────────────────────────┘
```

## Core Service Components

### 1. Backend REST API & WebSocket Streaming Server
- **Framework**: FastAPI (Python 3.10+) running on Uvicorn.
- **WebSocket Endpoint**: `/ws/interview/{session_id}` handles bi-directional real-time audio chunk STT and vision frame analysis at controlled 5–10 FPS.

### 2. Interview State Machine
Sessions transition through 9 explicit states persisted in MongoDB:
`CREATED` → `READY` → `QUESTION_ACTIVE` → `ANSWERING` → `QUESTION_COMPLETED` → `COMPLETED` → `ANALYZING` → `FEEDBACK_READY` / `FAILED`.

### 3. Speech Processing Module (`services/speech_service.py`)
- **STT Engine**: `faster-whisper` quantized CPU inference (`tiny.en`, `int8`).
- **Filler Word Detector**: Pattern matcher for `um`, `uh`, `like`, `actually`, `basically`, etc.
- **Dynamic WPM & Pause Analyzer**: Calculates Words-Per-Minute and silence duration.

### 4. Vision Processing Module (`services/vision_service.py`)
- **Computer Vision**: OpenCV + MediaPipe Face Mesh & Head Pose estimation.
- **Metrics**: Eye Contact %, Face Visibility %, Head Yaw/Pitch, and Facial Expression classification.

### 5. Scoring & Gemini LLM Feedback
- **Scoring Engine**: Decoupled Technical Knowledge vs Communication & Presentation metrics.
- **Gemini Service**: Generates qualitative feedback with deterministic fallback when API key is unconfigured or unreachable.

### 6. Video Privacy & Background TTL Worker
- Videos saved temporarily to `temp/interviews/<session_id>.webm`.
- Allowed 1-time replay; deleted immediately upon playback/modal close or purged via background TTL task.
