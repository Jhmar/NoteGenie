import uvicorn
import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting NoteGenie - AI Academic Assistant")
    print("=" * 60)
    print("🌐 Server URL: http://localhost:8000")
    print("📎 Click here: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("=" * 60)
    print("🔄 Auto-reload enabled (watching src/ only)")
    print("🛑 Press CTRL+C to stop")
    print("=" * 60)

    uvicorn.run(
        "src.main:app",
        host="localhost",
        port=8000,
        reload=True,
        reload_dirs=["src"],          # only watch src/ for changes
        reload_excludes=[
            "venv/*",
            ".venv/*",
            "*.pyc",
            "__pycache__/*",
            "uploads/*",
            "*.db",
        ]
    )