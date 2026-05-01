"""
Dashboard Routes for NoteGenie
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from src.models.user import get_db, User, UserDocument, UserActivity
from src.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    current_user = Depends(get_current_active_user)
):
    """Dashboard page"""
    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request,
            "user": current_user
        }
    )

@router.get("/stats")
async def get_user_stats(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user statistics"""
    
    # Count documents by type
    total_docs = db.query(UserDocument).filter(
        UserDocument.user_id == current_user.id
    ).count()
    
    audio_count = db.query(UserDocument).filter(
        UserDocument.user_id == current_user.id,
        UserDocument.file_type.in_(['stt', 'tts'])
    ).count()
    
    summary_count = db.query(UserDocument).filter(
        UserDocument.user_id == current_user.id,
        UserDocument.file_type == 'summary'
    ).count()
    
    questions_count = db.query(UserDocument).filter(
        UserDocument.user_id == current_user.id,
        UserDocument.file_type == 'questions'
    ).count()
    
    return {
        "stats": {
            "total_documents": total_docs,
            "audio_files": audio_count,
            "summaries": summary_count,
            "questions": questions_count
        }
    }