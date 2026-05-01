from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.config import BASE_DIR

templates = Jinja2Templates(directory=BASE_DIR / "templates")

async def register_page(request: Request):
    """Register page route"""
    return templates.TemplateResponse("register.html", {"request": request})

async def home(request: Request):
    """Homepage route"""
    return templates.TemplateResponse("index.html", {"request": request})

async def login_page(request: Request):
    """Login page route"""
    return templates.TemplateResponse("login.html", {"request": request})

async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "NoteGenie"}
