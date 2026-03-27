"""
SmartStudy API Routes - AI Learning Intervention System
Assembled sub-router package for chat, context, study plans, and video notes.
"""
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.models.user import User
from app.utils.auth import get_current_user

from app.routes.smartstudy.chat import router as chat_router
from app.routes.smartstudy.context import router as context_router
from app.routes.smartstudy.study_plans import router as study_plans_router
from app.routes.smartstudy.video_notes import router as video_notes_router
from app.routes.smartstudy.quizzes import router as quizzes_router
from app.routes.smartstudy.diagrams import router as diagrams_router

router = APIRouter(prefix="/api/v1/smartstudy", tags=["SmartStudy"])

router.include_router(chat_router)
router.include_router(context_router)
router.include_router(study_plans_router)
router.include_router(video_notes_router)
router.include_router(quizzes_router)
router.include_router(diagrams_router)


@router.get("/audio/{filename}", operation_id="serve_audio_file", summary="Serve cached audio MP3")
async def serve_audio(filename: str):
    """Serve a generated audio summary MP3 file."""
    # Sanitize filename to prevent path traversal
    safe_name = os.path.basename(filename)
    audio_dir = os.path.abspath(
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "audio_cache")
    )
    filepath = os.path.abspath(os.path.join(audio_dir, safe_name))

    # Verify resolved path is still within audio_dir
    if not filepath.startswith(audio_dir):
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(filepath, media_type="audio/mpeg", filename=safe_name)
