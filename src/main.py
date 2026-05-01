from contextlib import asynccontextmanager
from pathlib import Path
import sys

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ── Path setup (must happen before any src.* imports) ────────────────────────
BASE_DIR = Path(__file__).parent.parent   # project root  (NoteGenie_project/)
SRC_DIR  = Path(__file__).parent          # src/

# Allow both  `import routes.X`  and  `from src.X import …`
sys.path.insert(0, str(SRC_DIR))          # makes  `import routes.X`  work
sys.path.insert(0, str(BASE_DIR))         # makes  `from src.X import …`  work

# ── Route imports ─────────────────────────────────────────────────────────────
import routes.main_routes          as main_routes
import routes.ocr_routes           as ocr_routes
import routes.pdf_routes           as pdf_routes
import routes.tts_routes           as tts_routes
import routes.stt_routes           as stt_routes
import routes.summarization_routes as summarization_routes
import routes.question_routes      as question_routes
import routes.auth_routes          as auth_routes
import routes.dashboard_routes     as dashboard_routes
import routes.analytics_routes     as analytics_routes
import routes.file_routes          as file_routes
import routes.document_routes      as document_routes
import routes.youtube_routes       as youtube_routes

from src.models.user         import init_db, get_db
from src.auth.dependencies   import get_current_active_user

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ── Lifespan (replaces deprecated @app.on_event) ─────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    print("=" * 60)
    print("NoteGenie - AI-Powered Academic Assistant")
    print("=" * 60)
    print(f"Project root : {BASE_DIR}")
    print(f"Server URL   : http://localhost:8000")
    print(f"API Docs     : http://localhost:8000/docs")
    print(f"Auth System  : Active")
    print("=" * 60)
    yield
    # Shutdown
    print("\nNoteGenie shutting down...")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="NoteGenie",
    description="AI-Powered Academic Assistant",
    lifespan=lifespan,
)

# ── Static files ──────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# ── Page routes ───────────────────────────────────────────────────────────────
app.get("/")(main_routes.home)
app.get("/login")(main_routes.login_page)
app.get("/register")(main_routes.register_page)
app.get("/api/health")(main_routes.health_check)

@app.get("/dashboard")
async def get_dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": {"username": "test123", "id": "123"}},
    )

# ── API routes ────────────────────────────────────────────────────────────────

# OCR
app.post("/api/ocr")(ocr_routes.extract_text)
app.post("/api/upload")(ocr_routes.upload_file)

# PDF
app.post("/api/image-to-pdf")(pdf_routes.convert_images_to_pdf_endpoint)
app.get("/download-pdf/{filename}")(pdf_routes.download_pdf)

# Router-based (prefix lives inside each router file)
app.include_router(tts_routes.router)
app.include_router(stt_routes.router)
app.include_router(summarization_routes.router)
app.include_router(question_routes.router)
app.include_router(auth_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(analytics_routes.router)
app.include_router(file_routes.router)
app.include_router(document_routes.router)

# YouTube - prefix="/api/v1/youtube" is set inside youtube_routes.py
app.include_router(youtube_routes.router)