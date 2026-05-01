from fastapi import APIRouter
from . import auth, users, documents, ocr, stt, tts, summarize, questions, youtube

router = APIRouter()

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(documents.router)
router.include_router(ocr.router)
router.include_router(stt.router)
router.include_router(tts.router)
router.include_router(summarize.router)
router.include_router(questions.router)
router.include_router(youtube.router)  # Add this line