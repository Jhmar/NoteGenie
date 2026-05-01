import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Tuple
from fastapi import UploadFile

def save_uploaded_file(upload_file: UploadFile, directory: Path) -> Path:
    """Save uploaded file to directory and return path"""
    file_path = directory / upload_file.filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return file_path

def save_temp_file(upload_file: UploadFile) -> Tuple[str, str]:
    """Save uploaded file to temporary location"""
    file_extension = os.path.splitext(upload_file.filename)[1]
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        shutil.copyfileobj(upload_file.file, temp_file)
        temp_path = temp_file.name
    
    return temp_path, file_extension

def cleanup_temp_files(file_paths: List[str]):
    """Clean up temporary files"""
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except:
                pass

def get_file_info(file_path: Path) -> dict:
    """Get information about a file"""
    return {
        "filename": file_path.name,
        "size": file_path.stat().st_size,
        "created": file_path.stat().st_ctime,
        "modified": file_path.stat().st_mtime
    }

def validate_file_extension(filename: str, allowed_extensions: set) -> bool:
    """Check if file extension is allowed"""
    file_extension = Path(filename).suffix.lower()
    return file_extension in allowed_extensions