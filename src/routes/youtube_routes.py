"""
YouTube Notes Routes for NoteGenie
"""
from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import json
import uuid
from datetime import datetime

from src.models.user import get_db, UserDocument
from src.auth.dependencies import get_current_active_user
from src.services.youtube_note_service import YouTubeNoteService

router = APIRouter(prefix="/api/v1/youtube", tags=["YouTube"])

# Single shared service instance (models load once at startup)
youtube_service = YouTubeNoteService()


# ── Process ──────────────────────────────────────────────────────────────────

@router.post("/process")
async def process_youtube_video(
    url: str = Form(...),
    current_user=Depends(get_current_active_user),
):
    """
    Accept a YouTube URL, fetch its transcript, and return AI-generated notes.
    """
    url = url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required.")

    try:
        notes = youtube_service.process_video(url)
        return JSONResponse({
            "success": True,
            "notes": notes,
            "message": "Video processed successfully",
        })

    except ValueError as e:
        # Bad URL format
        raise HTTPException(status_code=400, detail=str(e))

    except RuntimeError as e:
        # Transcript unavailable, disabled captions, etc.
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        print(f"[youtube/process] Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the video.",
        )


# ── Save ─────────────────────────────────────────────────────────────────────

@router.post("/save")
async def save_youtube_notes(
    title: str = Form(...),
    notes_json: str = Form(...),
    folder_id: str = Form(None),
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Save generated YouTube notes as a document in the user's dashboard."""

    # ── Parse notes ──────────────────────────────────────────────────────────
    try:
        notes = json.loads(notes_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid notes JSON.")

    # ── Format as readable markdown ──────────────────────────────────────────
    duration_sec = notes.get("duration", 0)
    duration_str = (
        f"{int(duration_sec // 60)}m {int(duration_sec % 60)}s"
        if duration_sec
        else "Unknown"
    )

    lines = [
        f"# {notes.get('title', title)}",
        f"**Channel:** {notes.get('author', 'Unknown')}",
        f"**Duration:** {duration_str}",
        "",
        "## Overview",
        notes.get("overview", "No overview available."),
        "",
        "## Key Points",
    ]
    for point in notes.get("key_points", []):
        lines.append(f"- {point}")

    sections = notes.get("sections", [])
    if sections:
        lines += ["", "## Sections"]
        for sec in sections:
            lines.append(f"\n### {sec.get('title', 'Section')}")
            lines.append(sec.get("content", ""))

    questions = notes.get("questions", [])
    if questions:
        lines += ["", "## Study Questions"]
        for i, q in enumerate(questions, 1):
            lines.append(f"{i}. {q}")

    timestamps = notes.get("timestamps", [])
    if timestamps:
        lines += ["", "## Timestamps"]
        for t in timestamps:
            lines.append(f"- `{t.get('time', '00:00')}` — {t.get('text', '')}")

    content = "\n".join(lines)

    # ── Persist to database ───────────────────────────────────────────────────
    try:
        safe_title = title[:50].strip() or "YouTube Notes"
        doc_id = str(uuid.uuid4())
        new_doc = UserDocument(
            id=doc_id,
            user_id=current_user.id,
            folder_id=folder_id if folder_id and folder_id not in ("null", "undefined", "") else None,
            title=safe_title,
            filename=f"{safe_title[:30]}.md",
            file_type="youtube",
            content=content,
            created_at=datetime.utcnow(),
            last_opened=datetime.utcnow(),
        )
        db.add(new_doc)
        db.commit()

        return JSONResponse({
            "success": True,
            "document_id": doc_id,
            "message": "YouTube notes saved successfully",
        })

    except Exception as e:
        db.rollback()
        print(f"[youtube/save] DB error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save notes to database.")


# ── Info ─────────────────────────────────────────────────────────────────────

@router.get("/info")
async def get_youtube_info():
    """Return feature metadata."""
    return JSONResponse({
        "success": True,
        "feature": "YouTube Notes",
        "description": "Paste any YouTube URL to generate AI-powered study notes.",
        "ai_enabled": youtube_service.gemini_available,
        "status": "active",
    })