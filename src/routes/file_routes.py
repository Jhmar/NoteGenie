"""
File Routes for NoteGenie - Handle file preview and downloads
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from pathlib import Path
import os

from src.models.user import get_db, UserDocument
from src.auth.dependencies import get_current_active_user
from src.config import UPLOAD_DIR

router = APIRouter(prefix="/api/files", tags=["Files"])

@router.get("/{file_id}/preview")
async def preview_file(
    file_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get file preview (PDF/Images)"""
    
    file = db.query(UserDocument).filter(
        UserDocument.id == file_id,
        UserDocument.user_id == current_user.id
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = UPLOAD_DIR / file.filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    # Return appropriate response based on file type
    if file.filename.endswith('.pdf'):
        return FileResponse(
            path=file_path,
            media_type='application/pdf',
            filename=file.filename
        )
    elif file.filename.endswith(('.jpg', '.jpeg', '.png')):
        return FileResponse(
            path=file_path,
            media_type=f'image/{file.filename.split(".")[-1]}'
        )
    else:
        raise HTTPException(status_code=400, detail="Preview not available for this file type")

@router.get("/{file_id}/audio")
async def get_audio_file(
    file_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get audio file for playback"""
    
    file = db.query(UserDocument).filter(
        UserDocument.id == file_id,
        UserDocument.user_id == current_user.id
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = UPLOAD_DIR / file.filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        path=file_path,
        media_type='audio/mpeg',
        filename=file.filename
    )

@router.get("/{file_id}/content")
async def get_file_content(
    file_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get text content of file"""
    
    file = db.query(UserDocument).filter(
        UserDocument.id == file_id,
        UserDocument.user_id == current_user.id
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file.content:
        return JSONResponse({"content": file.content})
    else:
        return JSONResponse({"content": "No text content available for this file"})