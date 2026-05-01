"""
Speech-to-Text Routes for NoteGenie
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import os
from src.config import UPLOAD_DIR
from src.utils.stt_utils import speech_to_text, get_supported_languages, validate_audio_file
from src.utils.file_utils import save_temp_file, cleanup_temp_files

router = APIRouter(prefix="/api/stt", tags=["Speech-to-Text"])

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("en-US")
):
    """Transcribe audio file to text"""
    
    # Validate file
    is_valid, error_msg = validate_audio_file(file.filename)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Save temporary file
    temp_path, file_extension = save_temp_file(file)
    
    try:
        # Transcribe audio
        success, result, details = speech_to_text(temp_path, language)
        
        if success:
            return JSONResponse({
                "status": "success",
                "filename": file.filename,
                "transcribed_text": result,
                "details": details,
                "message": f"Successfully transcribed {details.get('words', 0)} words"
            })
        else:
            raise HTTPException(status_code=500, detail=result)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
        
    finally:
        # Clean up temp file
        cleanup_temp_files([temp_path])

@router.post("/transcribe-text")
async def transcribe_audio_with_text(
    file: UploadFile = File(...),
    language: str = Form("en-US")
):
    """Transcribe audio file and return only text (for simple use)"""
    
    # Validate file
    is_valid, error_msg = validate_audio_file(file.filename)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Save temporary file
    temp_path, file_extension = save_temp_file(file)
    
    try:
        # Transcribe audio
        success, result, details = speech_to_text(temp_path, language)
        
        if success:
            return JSONResponse({
                "status": "success",
                "text": result,
                "language": language
            })
        else:
            raise HTTPException(status_code=500, detail=result)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
        
    finally:
        # Clean up temp file
        cleanup_temp_files([temp_path])

@router.get("/languages")
async def list_languages():
    """Get supported languages for STT"""
    languages = get_supported_languages()
    return JSONResponse({
        "status": "success",
        "languages": languages,
        "count": len(languages)
    })