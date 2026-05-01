"""
Text-to-Speech Routes for NoteGenie
"""
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional
from src.config import UPLOAD_DIR
from src.utils.tts_utils import text_to_speech, get_available_languages, delete_audio_file

router = APIRouter(prefix="/api/tts", tags=["Text-to-Speech"])

@router.post("/generate")
async def generate_speech(
    text: str = Form(...),
    language: str = Form("en"),
    filename: Optional[str] = Form(None)
):
    """Generate speech from text"""
    
    if not text or len(text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # Limit text length to prevent abuse
    if len(text) > 5000:
        raise HTTPException(status_code=400, detail="Text too long. Maximum 5000 characters.")
    
    success, message, audio_filename = text_to_speech(text, language, filename)
    
    if success:
        return JSONResponse({
            "status": "success",
            "message": message,
            "audio_filename": audio_filename,
            "download_url": f"/api/tts/download/{audio_filename}",
            "preview_url": f"/api/tts/preview/{audio_filename}",
            "text_length": len(text)
        })
    else:
        raise HTTPException(status_code=500, detail=message)

@router.get("/languages")
async def list_languages():
    """Get available languages for TTS"""
    languages = get_available_languages()
    return JSONResponse({
        "status": "success",
        "languages": languages,
        "count": len(languages)
    })

@router.get("/download/{filename}")
async def download_audio(filename: str):
    """Download generated audio file"""
    file_path = UPLOAD_DIR / filename
    
    if file_path.exists() and filename.endswith('.mp3'):
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='audio/mpeg'
        )
    else:
        raise HTTPException(status_code=404, detail="Audio file not found")

@router.get("/preview/{filename}")
async def preview_audio(filename: str):
    """Stream audio for preview (HTML5 audio tag)"""
    file_path = UPLOAD_DIR / filename
    
    if file_path.exists() and filename.endswith('.mp3'):
        return FileResponse(
            path=file_path,
            media_type='audio/mpeg',
            headers={"Accept-Ranges": "bytes"}
        )
    else:
        raise HTTPException(status_code=404, detail="Audio file not found")

@router.delete("/delete/{filename}")
async def delete_audio(filename: str):
    """Delete audio file"""
    success = delete_audio_file(filename)
    
    if success:
        return JSONResponse({
            "status": "success",
            "message": f"Audio file '{filename}' deleted successfully"
        })
    else:
        raise HTTPException(status_code=404, detail="File not found or could not be deleted")