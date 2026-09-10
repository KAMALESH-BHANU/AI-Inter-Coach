import tempfile
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.api.auth import get_current_user
from app.db.models import UserModel
from app.services.resume_service import ResumeService
from app.utils.logger import logger

router = APIRouter(prefix="/api/resume", tags=["Resume Parsing"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user)
):
    filename = file.filename or "resume.pdf"
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format '{ext}'. Supported formats: PDF, DOCX, TXT."
        )

    # Save temporary file safely
    try:
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit.")

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        parsed_data = ResumeService.parse_resume(tmp_path, filename)
        return {
            "success": True,
            "filename": filename,
            "skills": parsed_data["skills"],
            "projects": parsed_data["projects"]
        }
    except Exception as e:
        logger.error(f"Failed to process uploaded resume: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
