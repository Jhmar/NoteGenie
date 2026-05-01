"""
Question Generator Routes for NoteGenie
Supports: comprehension, mcq, definition, comparison, reasoning, process, all
"""
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Optional
from src.utils.advanced_question_utils import AdvancedQuestionGenerator

router = APIRouter(prefix="/api/questions", tags=["Question Generator"])

question_gen = AdvancedQuestionGenerator()

# ── Helper: format questions as plain text ─────────────────────────────────

def _format_text(questions: list, total: int) -> str:
    out = f"📚 GENERATED QUESTIONS\n{'='*50}\n\n"
    for i, q in enumerate(questions, 1):
        out += f"{i}. [{q.get('type','').upper()}] {q.get('question','')}\n"
        if q.get('options'):
            for j, opt in enumerate(q['options']):
                mark = " ✓" if j == q.get('correct_index') else ""
                out += f"   {chr(65+j)}. {opt}{mark}\n"
        elif q.get('answer'):
            out += f"   Answer: {q['answer']}\n"
        out += "\n"
    out += f"{'='*50}\nTotal: {total} questions"
    return out


# ── /generate  (general — all types mixed) ────────────────────────────────

@router.post("/generate")
async def generate_questions(
    text: str = Form(...),
    num_questions: int = Form(5),
    format: Optional[str] = Form("json")
):
    if not text or len(text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Text too short (minimum 50 characters).")
    if not 1 <= num_questions <= 20:
        raise HTTPException(status_code=400, detail="num_questions must be 1–20.")
    try:
        result = question_gen.generate_questions(text, num_questions)
        if format == 'text':
            return PlainTextResponse(_format_text(result['questions'], result['total_questions']))
        return JSONResponse({
            "status": "success",
            "questions": result['questions'],
            "stats": result['stats'],
            "total_generated": result['total_questions'],
            "message": f"Generated {result['total_questions']} questions ({'AI' if question_gen.use_ai else 'rule-based'})"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {e}")


# ── /generate-typed  (specific type: comprehension / mcq / definition / …) ─

@router.post("/generate-typed")
async def generate_typed_questions(
    text: str = Form(...),
    question_type: str = Form("comprehension"),  # comprehension | mcq | definition | comparison | reasoning | process | all
    num_questions: int = Form(5),
    format: Optional[str] = Form("json")
):
    """
    Generate questions of a specific type.
    question_type: comprehension | mcq | definition | comparison | reasoning | process | all
    """
    if not text or len(text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Text too short (minimum 50 characters).")
    if not 1 <= num_questions <= 20:
        raise HTTPException(status_code=400, detail="num_questions must be 1–20.")

    valid_types = {"comprehension","mcq","definition","comparison","reasoning","process","all"}
    if question_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid type. Choose from: {', '.join(sorted(valid_types))}")

    try:
        sentences  = question_gen.extract_key_sentences(text, max_sentences=15)
        key_terms  = question_gen.extract_key_terms(text, max_terms=15)
        questions  = []

        if question_type in ("comprehension", "all"):
            questions += question_gen.generate_comprehension_questions(sentences, n=num_questions)

        if question_type in ("mcq", "all"):
            questions += question_gen.generate_mcq_questions(key_terms, sentences)

        if question_type in ("definition", "all"):
            questions += question_gen.generate_definition_questions(key_terms, text)

        if question_type in ("comparison", "all"):
            questions += question_gen.generate_comparison_questions(key_terms)

        if question_type in ("reasoning", "all"):
            questions += question_gen.generate_reasoning_questions(sentences, n=num_questions)

        if question_type in ("process", "all"):
            questions += question_gen.generate_process_questions(sentences, n=num_questions)

        # If AI is available and we still need more, use it to fill up
        if question_gen.use_ai and (len(questions) < num_questions or question_type == "all"):
            ai_qs = question_gen.generate_ai_questions(text, num_questions=num_questions)
            # Tag them with the requested type if specific
            if question_type != "all":
                for q in ai_qs:
                    q['type'] = question_type
            questions = ai_qs + questions  # AI first for quality

        # Deduplicate and trim
        seen, unique = set(), []
        for q in questions:
            key = q.get('question','')[:60]
            if key not in seen:
                seen.add(key)
                unique.append(q)

        unique = unique[:num_questions]

        if format == 'text':
            return PlainTextResponse(_format_text(unique, len(unique)))

        return JSONResponse({
            "status": "success",
            "question_type": question_type,
            "questions": unique,
            "total_generated": len(unique),
            "message": f"Generated {len(unique)} {question_type} questions"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {e}")


# ── /generate-mcq ────────────────────────────────────────────────────────────

@router.post("/generate-mcq")
async def generate_mcq_questions(
    text: str = Form(...),
    num_questions: int = Form(3)
):
    if not text or len(text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Text too short.")
    if not 1 <= num_questions <= 10:
        raise HTTPException(status_code=400, detail="num_questions must be 1–10.")
    try:
        sentences = question_gen.extract_key_sentences(text, max_sentences=10)
        terms     = question_gen.extract_key_terms(text, max_terms=15)
        mcqs      = question_gen.generate_mcq_questions(terms, sentences)[:num_questions]
        return JSONResponse({"status":"success","questions":mcqs,"total_mcq":len(mcqs),
                             "message":f"Generated {len(mcqs)} MCQ questions"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCQ generation failed: {e}")


# ── /generate-definitions ─────────────────────────────────────────────────────

@router.post("/generate-definitions")
async def generate_definition_questions(
    text: str = Form(...),
    num_questions: int = Form(3)
):
    if not text or len(text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Text too short.")
    if not 1 <= num_questions <= 10:
        raise HTTPException(status_code=400, detail="num_questions must be 1–10.")
    try:
        terms  = question_gen.extract_key_terms(text, max_terms=10)
        defs   = question_gen.generate_definition_questions(terms, text)[:num_questions]
        return JSONResponse({"status":"success","questions":defs,"total_definitions":len(defs),
                             "message":f"Generated {len(defs)} definition questions"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Definition question generation failed: {e}")


# ── /generate-ai ──────────────────────────────────────────────────────────────

@router.post("/generate-ai")
async def generate_ai_questions(
    text: str = Form(...),
    num_questions: int = Form(5)
):
    if not text or len(text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Text too short.")
    if not question_gen.use_ai:
        raise HTTPException(status_code=400, detail="AI model not available.")
    try:
        ai_qs = question_gen.generate_ai_questions(text, num_questions)
        return JSONResponse({"status":"success","questions":ai_qs,"total_generated":len(ai_qs),
                             "message":f"Generated {len(ai_qs)} AI questions"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI question generation failed: {e}")


# ── /types ────────────────────────────────────────────────────────────────────

@router.get("/types")
async def get_question_types():
    return JSONResponse({
        "status": "success",
        "ai_available": question_gen.use_ai,
        "question_types": [
            {"id":"comprehension","name":"Comprehension","description":"Tests understanding of concepts","example":"Explain how neural networks process data."},
            {"id":"mcq",          "name":"Multiple Choice","description":"4-option questions with one correct answer","example":"Which of the following describes backpropagation?"},
            {"id":"definition",   "name":"Definition","description":"Define key terms","example":"What is gradient descent?"},
            {"id":"comparison",   "name":"Comparison","description":"Compare and contrast concepts","example":"What is the difference between supervised and unsupervised learning?"},
            {"id":"reasoning",    "name":"Reasoning","description":"Why/because questions","example":"Why is feature scaling important?"},
            {"id":"process",      "name":"Process","description":"How does X work questions","example":"How does backpropagation update weights?"},
            {"id":"all",          "name":"All Types","description":"Mix of all question types","example":"Generates a varied set"},
        ]
    })


# ── /info ─────────────────────────────────────────────────────────────────────

@router.get("/info")
async def get_model_info():
    return JSONResponse({
        "status": "success",
        "model": {
            "type": "AI-powered" if question_gen.use_ai else "Rule-based",
            "name": "Gemini 2.0 Flash" if question_gen.use_ai else "Rule-based NLP",
            "capabilities": ["Comprehension","MCQ","Definition","Comparison","Reasoning","Process","All types"],
            "status": "active"
        }
    })