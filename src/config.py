import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env file ────────────────────────────────────────────────────────────
load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# ── AI / API Keys ─────────────────────────────────────────────────────────────
# Get a free Gemini API key at: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ── Tesseract (OCR) ───────────────────────────────────────────────────────────
TESSERACT_PATHS = [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    r'C:\Users\{USERNAME}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
]

# ── Allowed file types ────────────────────────────────────────────────────────
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
ALLOWED_PDF_EXTENSIONS   = {'.pdf'}
ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.ogg'}

# ── File size limits ──────────────────────────────────────────────────────────
MAX_IMAGE_SIZE = 10  * 1024 * 1024   # 10 MB
MAX_PDF_SIZE   = 50  * 1024 * 1024   # 50 MB
MAX_AUDIO_SIZE = 100 * 1024 * 1024   # 100 MB

# ── App metadata ──────────────────────────────────────────────────────────────
APP_NAME        = "NoteGenie"
APP_DESCRIPTION = "AI-Powered Academic Assistant"
APP_VERSION     = "1.0.0"