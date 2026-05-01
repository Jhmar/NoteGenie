"""
Note Summarization Routes for NoteGenie
"""
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional
from src.utils.summarization_utils import Summarizer, get_summary_stats, validate_text_length

router = APIRouter(prefix="/api/summarization", tags=["Note Summarization"])

# Initialize summarizer
summarizer = Summarizer()

@router.post("/summarize")
async def summarize_text(
    text: str = Form(...),
    method: str = Form("extractive"),
    num_sentences: Optional[int] = Form(3),
    max_length: Optional[int] = Form(150),
    min_length: Optional[int] = Form(50)
):
    """Summarize text using specified method"""
    
    # Validate text
    is_valid, error_msg = validate_text_length(text)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Validate method
    if method not in ["extractive", "abstractive"]:
        raise HTTPException(status_code=400, detail="Method must be 'extractive' or 'abstractive'")
    
    try:
        # Prepare kwargs based on method
        kwargs = {}
        if method == "extractive":
            if num_sentences < 1 or num_sentences > 10:
                raise HTTPException(status_code=400, detail="num_sentences must be between 1 and 10")
            kwargs['num_sentences'] = num_sentences
        else:  # abstractive
            if max_length < 30 or max_length > 500:
                raise HTTPException(status_code=400, detail="max_length must be between 30 and 500")
            if min_length < 10 or min_length > 200:
                raise HTTPException(status_code=400, detail="min_length must be between 10 and 200")
            if min_length >= max_length:
                raise HTTPException(status_code=400, detail="min_length must be less than max_length")
            kwargs['max_length'] = max_length
            kwargs['min_length'] = min_length
        
        # Generate summary
        summary, details = summarizer.summarize(text, method, **kwargs)
        
        # Get statistics
        stats = get_summary_stats(text, summary)
        
        return JSONResponse({
            "status": "success",
            "summary": summary,
            "details": {**details, **stats},
            "method": method,
            "message": f"Summary generated successfully using {method} method"
        })
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

@router.post("/summarize-extractive")
async def summarize_extractive(
    text: str = Form(...),
    num_sentences: int = Form(3)
):
    """Summarize text using extractive method (simplified endpoint)"""
    
    is_valid, error_msg = validate_text_length(text)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    if num_sentences < 1 or num_sentences > 10:
        raise HTTPException(status_code=400, detail="num_sentences must be between 1 and 10")
    
    try:
        summary, details = summarizer.summarize(text, "extractive", num_sentences=num_sentences)
        stats = get_summary_stats(text, summary)
        
        return JSONResponse({
            "status": "success",
            "summary": summary,
            "details": {**details, **stats}
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extractive summarization failed: {str(e)}")

@router.post("/summarize-abstractive")
async def summarize_abstractive(
    text: str = Form(...),
    max_length: int = Form(150),
    min_length: int = Form(50)
):
    """Summarize text using abstractive method (simplified endpoint)"""
    
    is_valid, error_msg = validate_text_length(text)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    if max_length < 30 or max_length > 500:
        raise HTTPException(status_code=400, detail="max_length must be between 30 and 500")
    if min_length < 10 or min_length > 200:
        raise HTTPException(status_code=400, detail="min_length must be between 10 and 200")
    if min_length >= max_length:
        raise HTTPException(status_code=400, detail="min_length must be less than max_length")
    
    try:
        summary, details = summarizer.summarize(
            text, 
            "abstractive", 
            max_length=max_length, 
            min_length=min_length
        )
        stats = get_summary_stats(text, summary)
        
        return JSONResponse({
            "status": "success",
            "summary": summary,
            "details": {**details, **stats}
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Abstractive summarization failed: {str(e)}")

@router.get("/methods")
async def get_methods():
    """Get available summarization methods"""
    return JSONResponse({
        "status": "success",
        "methods": [
            {
                "id": "extractive",
                "name": "Extractive Summarization",
                "description": "Extracts the most important sentences from the original text",
                "parameters": [
                    {"name": "num_sentences", "type": "integer", "range": "1-10", "default": 3}
                ]
            },
            {
                "id": "abstractive",
                "name": "Abstractive Summarization",
                "description": "Generates new concise text that captures the main ideas",
                "parameters": [
                    {"name": "max_length", "type": "integer", "range": "30-500", "default": 150},
                    {"name": "min_length", "type": "integer", "range": "10-200", "default": 50}
                ]
            }
        ]
    })