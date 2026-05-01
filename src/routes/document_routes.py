"""
Document Routes for NoteGenie - Handle saving and retrieving notes
"""
from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import json

from src.models.user import get_db, UserDocument, Folder
from src.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/api/documents", tags=["Documents"])

@router.post("/save")
async def save_document(
    title: str = Form(...),
    content: str = Form(...),
    file_type: str = Form(...),
    folder_id: str = Form(None),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Save a document to user's notes"""
    
    # Create new document
    doc_id = str(uuid.uuid4())
    new_doc = UserDocument(
        id=doc_id,
        user_id=current_user.id,
        folder_id=folder_id if folder_id and folder_id != 'null' else None,
        title=title,
        filename=f"{title[:30]}.txt",
        file_type=file_type,
        content=content,
        created_at=datetime.utcnow(),
        last_opened=datetime.utcnow()
    )
    
    db.add(new_doc)
    db.commit()
    
    return JSONResponse({
        "success": True,
        "document_id": doc_id,
        "message": "Document saved successfully"
    })

@router.get("/list")
async def get_documents(
    folder_id: str = None,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all documents for user"""
    
    query = db.query(UserDocument).filter(UserDocument.user_id == current_user.id)
    
    if folder_id and folder_id != 'all':
        query = query.filter(UserDocument.folder_id == folder_id)
    
    documents = query.order_by(UserDocument.last_opened.desc()).all()
    
    result = []
    for doc in documents:
        result.append({
            "id": doc.id,
            "title": doc.title or doc.filename,
            "type": doc.file_type,
            "size": doc.file_size or 0,
            "last_opened": doc.last_opened.isoformat() if doc.last_opened else None,
            "folder_id": doc.folder_id,
            "is_favorite": doc.is_favorite,
            "icon": get_icon_for_type(doc.file_type)
        })
    
    return JSONResponse({"documents": result})


@router.get("/{doc_id}")
async def get_document(
    doc_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a single document with full content"""
    doc = db.query(UserDocument).filter(
        UserDocument.id == doc_id,
        UserDocument.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Update last_opened
    doc.last_opened = datetime.utcnow()
    db.commit()

    return JSONResponse({
        "id":          doc.id,
        "title":       doc.title or doc.filename,
        "content":     doc.content or "",
        "file_type":   doc.file_type,
        "size":        doc.file_size or 0,
        "last_opened": doc.last_opened.isoformat() if doc.last_opened else None,
        "folder_id":   doc.folder_id,
        "icon":        get_icon_for_type(doc.file_type)
    })

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a document"""
    
    doc = db.query(UserDocument).filter(
        UserDocument.id == doc_id,
        UserDocument.user_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db.delete(doc)
    db.commit()
    
    return JSONResponse({"success": True, "message": "Document deleted"})

@router.post("/move")
async def move_document(
    doc_id: str = Form(...),
    folder_id: str = Form(...),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Move document to folder"""
    
    doc = db.query(UserDocument).filter(
        UserDocument.id == doc_id,
        UserDocument.user_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc.folder_id = folder_id if folder_id != 'none' else None
    db.commit()
    
    return JSONResponse({"success": True, "message": "Document moved"})

@router.post("/rename")
async def rename_document(
    doc_id: str = Form(...),
    new_title: str = Form(...),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Rename document"""
    
    doc = db.query(UserDocument).filter(
        UserDocument.id == doc_id,
        UserDocument.user_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc.title = new_title
    db.commit()
    
    return JSONResponse({"success": True, "message": "Document renamed"})

# Helper function
def get_icon_for_type(file_type: str) -> str:
    icons = {
        'ocr': 'fa-file-pdf',
        'stt': 'fa-file-audio',
        'tts': 'fa-file-audio',
        'summary': 'fa-file-alt',
        'questions': 'fa-question-circle',
        'pdf': 'fa-file-pdf'
    }
    return icons.get(file_type, 'fa-file-alt')

# Folder routes
@router.post("/folders/create")
async def create_folder(
    name: str = Form(...),
    color: str = Form("#f59e0b"),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new folder"""
    
    folder = Folder(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        name=name,
        color=color,
        created_at=datetime.utcnow()
    )
    
    db.add(folder)
    db.commit()
    
    return JSONResponse({
        "success": True,
        "folder_id": folder.id,
        "message": f"Folder '{name}' created"
    })

@router.get("/folders/list")
async def get_folders(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all folders for user"""
    
    folders = db.query(Folder).filter(Folder.user_id == current_user.id).all()
    
    result = [{"id": "all", "name": "All Notes", "count": 0}]
    for folder in folders:
        count = db.query(UserDocument).filter(
            UserDocument.folder_id == folder.id
        ).count()
        result.append({
            "id": folder.id,
            "name": folder.name,
            "color": folder.color,
            "count": count
        })
    
    return JSONResponse({"folders": result})