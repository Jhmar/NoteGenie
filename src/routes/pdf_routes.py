from fastapi import UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from typing import List
import os
from src.config import UPLOAD_DIR, ALLOWED_IMAGE_EXTENSIONS
from src.utils.pdf_utils import convert_images_to_pdf
from src.utils.file_utils import save_temp_file, cleanup_temp_files, validate_file_extension

async def convert_images_to_pdf_endpoint(files: List[UploadFile] = File(...)):
    """Convert multiple images to a single PDF"""
    
    if len(files) == 0:
        return JSONResponse({
            "status": "error",
            "message": "No files uploaded"
        }, status_code=400)
    
    temp_files = []
    image_paths = []
    
    try:
        # Validate and save all uploaded files
        for file in files:
            if not validate_file_extension(file.filename, ALLOWED_IMAGE_EXTENSIONS):
                return JSONResponse({
                    "status": "error",
                    "message": f"Unsupported file type. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
                }, status_code=400)
            
            temp_path, _ = save_temp_file(file)
            temp_files.append(temp_path)
            image_paths.append(temp_path)
        
        # Create output PDF file
        output_filename = f"converted_{len(files)}_images.pdf"
        output_path = UPLOAD_DIR / output_filename
        
        # Convert images to PDF
        success, message = convert_images_to_pdf(image_paths, str(output_path))
        
        if success:
            return JSONResponse({
                "status": "success",
                "message": message,
                "pdf_filename": output_filename,
                "file_size": output_path.stat().st_size,
                "page_count": len(files),
                "download_url": f"/download-pdf/{output_filename}"
            })
        else:
            return JSONResponse({
                "status": "error",
                "message": message
            }, status_code=500)
            
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }, status_code=500)
        
    finally:
        # Clean up temporary files
        cleanup_temp_files(temp_files)

async def download_pdf(filename: str):
    """Download generated PDF file"""
    file_path = UPLOAD_DIR / filename
    
    if file_path.exists():
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/pdf'
        )
    else:
        return JSONResponse({
            "status": "error",
            "message": "File not found"
        }, status_code=404)