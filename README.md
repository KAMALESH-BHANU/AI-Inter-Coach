# AI Interview Coach — Complete AI-Powered Interview Platform

Production-style, modular, end-to-end AI Interview Coach platform built with FastAPI, React (Vite + Tailwind CSS), OpenCV, MediaPipe, `faster-whisper`, ReportLab, and Gemini LLM integration.

---

## Key Features

- **Candidate Authentication**: JWT auth, bcrypt password hashing, protected routes, profile and history tracking.
- **Resume & Skill Analysis**: PDF/DOCX/TXT parser with controlled taxonomy skill & project technology extraction.
- **Searchable Multi-Select Skill Selector**: Predefined 45+ skills taxonomy dropdown.
- **Strict 10-Question Interview Engine**: Server-side validated distribution (3 Project, 5 Technical Skill, 2 Pseudocode/Output prediction questions).
- **Explicit 9-State Machine**: Session recovery across WebSocket disconnections (`CREATED` → `READY` → `QUESTION_ACTIVE` → `ANSWERING` → `QUESTION_COMPLETED` → `COMPLETED` → `ANALYZING` → `FEEDBACK_READY` / `FAILED`).
- **Real-Time Speech & Vision Analysis**:
  - `faster-whisper` quantized CPU inference STT.
  - Filler word detection (`um`, `uh`, `like`, `actually`, `basically`, etc.), WPM calculator, and pause analyzer.
  - OpenCV + MediaPipe Eye Contact %, Face Visibility, Head Pose, and Expression classification at controlled 5–10 FPS.
- **Decoupled Scoring Engine**: Independent scores for Technical Knowledge, Answer Quality, Communication, Project Understanding, Presentation, Eye Contact, and Speech Fluency.
- **Gemini LLM Feedback & Fallback**: Qualitative feedback generation with deterministic fallback if Gemini API is offline.
- **Privacy & Auto-Cleanup TTL Worker**: 1-time video replay policy with automatic server-side deletion upon playback/close, plus background TTL worker.
- **Downloadable PDF Reports**: Styled multi-page evaluation reports generated via ReportLab.

---

## Environment Configuration (`backend/.env`)

```env
PROJECT_NAME="AI Interview Coach"
ENV="development"
PORT=8000

MONGODB_URI="mongodb://localhost:27017"
MONGODB_DB_NAME="ai_interview_coach"

JWT_SECRET="dev-secret-key-ai-interview-coach-2026"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440

GEMINI_API_KEY="your_gemini_api_key_here"
GEMINI_MODEL="gemini-2.5-flash"

WHISPER_MODEL="tiny.en"
WHISPER_COMPUTE_TYPE="int8"
FRAME_SAMPLE_FPS=5
VIDEO_TTL_MINUTES=60
TEMP_DIR="./temp/interviews"

FRONTEND_URL="http://localhost:5173"
```

---

## Local Development Setup & Commands

### 1. Backend Setup (FastAPI + Python 3.10+)

```bash
# Navigate to project root
cd "c:\Users\Kamalesh Banu\Documents\PROJECTS\AI-Inter-coach"

# Create & activate virtual environment (optional)
python -m venv venv
venv\Scripts\activate

# Install requirements
pip install -r backend/requirements.txt

# Seed question banks
python backend/data/questions/seed_questions.py

# Run unit test suite
$env:PYTHONPATH="backend"; python -m pytest backend/tests/

# Start FastAPI backend server
uvicorn app.main:app --reload --port 8000 --app-dir backend
```

### 2. Frontend Setup (React + Vite + Tailwind CSS)

```bash
# Navigate to frontend directory
cd frontend

# Install frontend packages
npm install

# Start Vite development server
npm run dev
```

Visit `http://localhost:5173` in your browser.

---

## Verification & Testing

Run all automated pytest suites:
```powershell
$env:PYTHONPATH="backend"; python -m pytest backend/tests/
```

Test coverage includes:
- `test_api_endpoints.py`: User authentication, JWT tokens, skills taxonomy.
- `test_question_validation.py`: 10-question distribution rules, duplicate ID rejection, skill matching.
- `test_resume_service.py`: Document parsing and skill extraction.
- `test_speech_service.py`: STT, filler word detection, WPM, and pause calculation.
- `test_vision_service.py`: Face detection and gaze estimation metrics.
- `test_scoring_and_gemini.py`: Independent scoring engine and Gemini fallback behavior.
- `test_report_service.py`: PDF document generation.
