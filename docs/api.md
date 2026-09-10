# API Documentation — AI Interview Coach

## Authentication Endpoints (`/api/auth`)
- `POST /api/auth/register` — Registers candidate account with password hashing (`bcrypt`) & JWT token.
- `POST /api/auth/login` — Authenticates user credentials and returns JWT bearer token.
- `GET /api/auth/me` — Returns current authenticated candidate profile.

## Resume & Question Endpoints
- `POST /api/resume/upload` — Uploads PDF/DOCX/TXT resume; parses skills taxonomy and project information.
- `GET /api/questions/skills` — Returns searchable multi-select taxonomy skills list.

## Interview Session Endpoints (`/api/interview`)
- `POST /api/interview/create` — Initializes 10-question interview session (3 project, 5 tech, 2 pseudocode).
- `GET /api/interview/{session_id}` — Retrieves current active session state for recovery.
- `POST /api/interview/{session_id}/answer` — Saves answer metrics and advances question index.
- `POST /api/interview/{session_id}/complete` — Finalizes interview, runs scoring engine & Gemini LLM feedback.
- `GET /api/interview/{session_id}/results` — Retrieves complete score breakdown and feedback.
- `POST /api/interview/{session_id}/delete-video` — Triggers video deletion per 1-time replay policy.
- `GET /api/interview/{session_id}/pdf` — Downloads styled multi-page PDF evaluation report.
- `GET /api/interview/history/user` — Returns candidate interview history for dashboard analytics.

## Real-Time WebSocket (`/ws/interview/{session_id}`)
- Receives JSON messages containing base64 camera frames or audio chunks.
- Emits real-time `vision_update` and `speech_update` metric events.
