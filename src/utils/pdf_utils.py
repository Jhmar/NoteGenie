import img2pdf
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image
from typing import List, Tuple
import os

def convert_images_to_pdf(img_paths: List[str], output_path: str) -> Tuple[bool, str]:
    """Convert multiple images to a single PDF"""
    try:
        # Method 1: Using img2pdf (better quality)
        with open(output_path, "wb") as pdf_file:
            pdf_file.write(img2pdf.convert(img_paths))
        
        return True, f"PDF created successfully with {len(img_paths)} pages"
        
    except Exception as e:
        try:
            # Method 2: Fallback using reportlab
            return convert_images_to_pdf_reportlab(img_paths, output_path)
        except Exception as e2:
            return False, f"Failed to create PDF: {str(e2)}"

def convert_images_to_pdf_reportlab(img_paths: List[str], output_path: str) -> Tuple[bool, str]:
    """Convert images to PDF using reportlab (fallback)"""
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    successful = 0
    
    for img_path in img_paths:
        try:
            img = Image.open(img_path)
            img_width, img_height = img.size
            
            # Calculate scaling
            scale_width = width / img_width
            scale_height = height / img_height
            scale = min(scale_width, scale_height) * 0.9
            
            # Calculate position to center
            x = (width - (img_width * scale)) / 2
            y = (height - (img_height * scale)) / 2
            
            # Draw image
            c.drawImage(img_path, x, y, 
                       width=img_width*scale, 
                       height=img_height*scale)
            c.showPage()
            successful += 1
        except:
            continue
    
    if successful > 0:
        c.save()
        return True, f"PDF created with {successful} images (reportlab)"
    else:
        return False, "Failed to process any images"