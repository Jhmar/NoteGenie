import pytesseract
from PIL import Image
import PyPDF2
import subprocess
import os
from typing import Optional
from src.config import TESSERACT_PATHS

def setup_tesseract() -> bool:
    """Setup Tesseract OCR path"""
    # Try to find tesseract using 'where' command
    try:
        result = subprocess.run(['where', 'tesseract'], 
                              capture_output=True, text=True, shell=True)
        if result.stdout and os.path.exists(result.stdout.strip()):
            path = result.stdout.strip()
            print(f"✅ Found Tesseract at: {path}")
            pytesseract.pytesseract.tesseract_cmd = path
            return True
    except:
        pass
    
    # Try common paths
    for path_template in TESSERACT_PATHS:
        path = path_template.replace('{USERNAME}', os.getenv('USERNAME', ''))
        if os.path.exists(path):
            print(f"✅ Found Tesseract at: {path}")
            pytesseract.pytesseract.tesseract_cmd = path
            return True
    
    # Last resort: check if tesseract is in PATH
    try:
        subprocess.run(['tesseract', '--version'], 
                      capture_output=True, text=True, shell=True)
        print("✅ Tesseract found in system PATH")
        return True
    except:
        print("❌ Tesseract not found. OCR will not work.")
        return False

def extract_text_from_image(image_path: str) -> str:
    """Extract text from an image using OCR"""
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text.strip() if text else "No text could be extracted from the image."
    except Exception as e:
        return f"Error processing image: {str(e)}"

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file"""
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n\n"
        
        return text.strip() if text else "No text could be extracted from the PDF."
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

def extract_text_from_file(file_path: str, file_extension: str) -> dict:
    """Extract text from file based on its type"""
    if file_extension.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']:
        extracted_text = extract_text_from_image(file_path)
        file_type = "image"
    elif file_extension.lower() == '.pdf':
        extracted_text = extract_text_from_pdf(file_path)
        file_type = "PDF"
    else:
        extracted_text = f"Unsupported file type: {file_extension}"
        file_type = "unsupported"
    
    return {
        "text": extracted_text,
        "type": file_type,
        "characters": len(extracted_text) if file_type in ["image", "PDF"] else 0
    }