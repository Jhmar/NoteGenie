"""
Advanced Question Generator for NoteGenie
Uses Google Gemini AI with a rule-based fallback (no transformers needed).
"""
import re
import os
import random
from typing import List, Dict

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

class AdvancedQuestionGenerator:
    """
    Generates study questions from any text input.

    Modes
    -----
    AI mode   : GROQ_API_KEY is set  → rich, contextual questions via Groq Llama3
    Rule mode : no API key             → deterministic NLP-based extraction (always works)
    """

    def __init__(self):
        self.use_ai = bool(GROQ_API_KEY)
        if self.use_ai:
            self.client = Groq(api_key=GROQ_API_KEY)
            print("✅ AdvancedQuestionGenerator: Groq AI ready")
        else:
            self.model = None
            print("⚠️  AdvancedQuestionGenerator: no GROQ_API_KEY – rule-based mode active")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _gemini(self, prompt: str) -> str:
        """Call Groq and return stripped text."""
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()

    def _truncate(self, text: str, max_chars: int = 12_000) -> str:
        """Keep text within Gemini's comfortable context window."""
        return text[:max_chars]

    # ── Text extraction helpers (used by routes directly) ─────────────────────

    def extract_key_sentences(self, text: str, max_sentences: int = 10) -> List[str]:
        """Return the longest / most information-dense sentences."""
        raw = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in raw if len(s.split()) > 6]
        # Rank by word count (longer = more content)
        ranked = sorted(sentences, key=lambda s: len(s.split()), reverse=True)
        # De-duplicate while preserving order
        seen, result = set(), []
        for s in ranked:
            key = s[:60]
            if key not in seen:
                seen.add(key)
                result.append(s)
            if len(result) >= max_sentences:
                break
        return result

    def extract_key_terms(self, text: str, max_terms: int = 15) -> List[str]:
        """Extract capitalised noun phrases (likely important concepts)."""
        raw_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        # Remove sentence-starters (first word of a sentence tends to be capitalised)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        starters = {s.split()[0] for s in sentences if s}

        seen, terms = set(), []
        for t in raw_terms:
            if t not in starters and t not in seen and len(t.split()) <= 4:
                seen.add(t)
                terms.append(t)
            if len(terms) >= max_terms:
                break
        return terms

    # ── Individual question-type generators ───────────────────────────────────

    def generate_definition_questions(self, terms: List[str], context: str) -> List[Dict]:
        """'What is X?' questions grounded in the source text."""
        questions = []
        sentences = re.split(r'(?<=[.!?])\s+', context)

        for term in terms[:5]:
            # Find the most relevant sentence containing the term
            relevant = [s for s in sentences if term.lower() in s.lower()]
            answer = relevant[0].strip() if relevant else f"Refer to the source text for the definition of {term}."
            questions.append({
                "type": "definition",
                "question": f"What is {term}?",
                "answer": answer,
                "term": term,
            })
        return questions

    def generate_comparison_questions(self, terms: List[str]) -> List[Dict]:
        """'What is the difference between X and Y?' questions."""
        questions = []
        pairs = [(terms[i], terms[j])
                 for i in range(min(len(terms), 4))
                 for j in range(i + 1, min(len(terms), 4))]
        for t1, t2 in pairs[:3]:
            questions.append({
                "type": "comparison",
                "question": f"What is the difference between {t1} and {t2}?",
                "answer": f"Compare {t1} and {t2} using evidence from the text.",
                "terms": [t1, t2],
            })
        return questions

    def generate_mcq_questions(self, terms: List[str], sentences: List[str]) -> List[Dict]:
        """Multiple-choice questions built from key terms."""
        questions = []
        if len(terms) < 4:
            return questions

        for i in range(min(3, len(terms))):
            correct = terms[i]
            distractors = [t for t in terms if t != correct]
            random.shuffle(distractors)
            options = [correct] + distractors[:3]
            random.shuffle(options)
            correct_index = options.index(correct)

            # Build a context-aware stem if possible
            stem_sentence = next(
                (s for s in sentences if correct.lower() in s.lower()), None
            )
            if stem_sentence:
                question_text = (
                    f"Based on the text, which term best fits: "
                    f'"{stem_sentence[:80].rstrip()}…"?'
                )
            else:
                question_text = f"Which of the following is a key concept discussed in the text?"

            questions.append({
                "type": "mcq",
                "question": question_text,
                "options": options,
                "correct_answer": correct,
                "correct_index": correct_index,
            })
        return questions

    def generate_comprehension_questions(self, sentences: List[str], n: int = 3) -> List[Dict]:
        """Open-ended comprehension questions from key sentences."""
        questions = []
        for sentence in sentences[:n]:
            short = sentence[:70].rstrip()
            questions.append({
                "type": "comprehension",
                "question": f"Explain the following in your own words: \"{short}…\"",
                "answer": sentence,
            })
        return questions

    def generate_reasoning_questions(self, sentences: List[str], n: int = 2) -> List[Dict]:
        """'Why…?' questions that encourage deeper analysis."""
        questions = []
        for sentence in sentences[:n]:
            # Strip leading connectives so the question reads naturally
            clean = re.sub(r'^(This|It|They|These|The)\s+', '', sentence).strip()
            questions.append({
                "type": "reasoning",
                "question": f"Why is it important that {clean[:70]}?",
                "answer": sentence,
            })
        return questions

    def generate_process_questions(self, sentences: List[str], n: int = 2) -> List[Dict]:
        """'How does…?' questions focused on mechanisms and processes."""
        questions = []
        for sentence in sentences[:n]:
            clean = re.sub(r'^(This|It|They|These|The)\s+', '', sentence).strip()
            questions.append({
                "type": "process",
                "question": f"How does {clean[:70]}?",
                "answer": sentence,
            })
        return questions

    # ── AI generation (Gemini) ────────────────────────────────────────────────

    def generate_ai_questions(self, text: str, num_questions: int = 5) -> List[Dict]:
        """
        Generate diverse questions via Gemini.
        Falls back to an empty list (caller will supplement with rule-based questions).
        """
        if not self.use_ai:
            return []

        excerpt = self._truncate(text)
        prompt = f"""You are an academic question generator.

Given the following text, generate exactly {num_questions} high-quality study questions.
Include a mix of: definition, comparison, reasoning, comprehension, and process questions.

For EACH question output exactly three lines:
  TYPE: <one of: definition | comparison | mcq | comprehension | reasoning | process>
  QUESTION: <the question>
  ANSWER: <a concise model answer>

Text:
{excerpt}

Questions:"""

        try:
            raw = self._gemini(prompt)
            questions = []
            current: Dict = {}

            for line in raw.splitlines():
                line = line.strip()
                if line.upper().startswith("TYPE:"):
                    if current.get("question"):
                        questions.append(current)
                    current = {"type": line.split(":", 1)[1].strip().lower()}
                elif line.upper().startswith("QUESTION:") and current:
                    current["question"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("ANSWER:") and current:
                    current["answer"] = line.split(":", 1)[1].strip()

            if current.get("question"):
                questions.append(current)

            return questions[:num_questions]

        except Exception as e:
            print(f"Gemini question generation failed: {e}")
            return []

    # ── Main entry point ──────────────────────────────────────────────────────

    def generate_questions(self, text: str, num_questions: int = 5) -> Dict:
        """
        Generate a diverse set of questions from `text`.
        Always returns a valid dict even if AI is unavailable.
        """
        sentences = self.extract_key_sentences(text, max_sentences=12)
        key_terms = self.extract_key_terms(text, max_terms=15)

        all_questions: List[Dict] = []

        # ── AI questions (best quality) ───────────────────────────────────────
        if self.use_ai:
            ai_qs = self.generate_ai_questions(text, num_questions=num_questions)
            all_questions.extend(ai_qs)

        # ── Rule-based fill-up ────────────────────────────────────────────────
        if len(all_questions) < num_questions:
            remaining = num_questions - len(all_questions)
            rule_pool: List[Dict] = []

            rule_pool.extend(self.generate_definition_questions(key_terms, text))
            rule_pool.extend(self.generate_comparison_questions(key_terms))
            rule_pool.extend(self.generate_mcq_questions(key_terms, sentences))
            rule_pool.extend(self.generate_comprehension_questions(sentences))
            rule_pool.extend(self.generate_reasoning_questions(sentences))
            rule_pool.extend(self.generate_process_questions(sentences))

            random.shuffle(rule_pool)
            all_questions.extend(rule_pool[:remaining])

        # ── Final trim & return ───────────────────────────────────────────────
        final = all_questions[:num_questions]

        return {
            "total_questions": len(final),
            "questions": final,
            "stats": {
                "sentences_analysed": len(sentences),
                "key_terms_found": len(key_terms),
                "ai_used": self.use_ai,
            },
        }