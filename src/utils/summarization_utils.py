"""
Note Summarization Utilities for NoteGenie
Extractive : TF-IDF sentence ranking  (no API key needed, always works)
Abstractive: Groq Llama3              (falls back to extractive if key missing)
"""
import os
import re
import nltk
import numpy as np
from typing import Tuple, Dict
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from dotenv import load_dotenv

load_dotenv()

# ── NLTK bootstrap ─────────────────────────────────────────────────────────
for _res, _path in [
    ('punkt',                    'tokenizers/punkt'),
    ('punkt_tab',                'tokenizers/punkt_tab'),
    ('stopwords',                'corpora/stopwords'),
]:
    try:
        nltk.data.find(_path)
    except LookupError:
        nltk.download(_res, quiet=True)

# ── Groq client (lazy-loaded) ───────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
_groq_client = None

def _get_groq():
    global _groq_client
    if _groq_client is None and GROQ_API_KEY:
        from groq import Groq
        _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client


class Summarizer:
    """Extractive and abstractive text summarization."""

    def __init__(self):
        self.stop_words = set(stopwords.words('english'))

    def clean_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?;:]', ' ', text)
        return text.strip()

    # ── Extractive ────────────────────────────────────────────────────────────

    def extractive_summarization(self, text: str, num_sentences: int = 3) -> Tuple[str, Dict]:
        """Pick the highest-scoring sentences using TF-IDF."""
        try:
            text      = self.clean_text(text)
            sentences = sent_tokenize(text)

            if len(sentences) <= num_sentences:
                return text, {
                    "method": "extractive",
                    "sentences_original": len(sentences),
                    "sentences_summary":  len(sentences),
                    "compression_ratio":  "100%",
                }

            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf      = vectorizer.fit_transform(sentences)
            scores     = np.array(tfidf.sum(axis=1)).flatten()
            top_idx    = sorted(scores.argsort()[-num_sentences:].tolist())
            summary    = ' '.join(sentences[i] for i in top_idx)

            return summary, {
                "method":              "extractive",
                "sentences_original":  len(sentences),
                "sentences_summary":   num_sentences,
                "compression_ratio":   f"{num_sentences/len(sentences)*100:.1f}%",
            }
        except Exception as e:
            raise Exception(f"Extractive summarization failed: {e}")

    # ── Abstractive ───────────────────────────────────────────────────────────

    def abstractive_summarization(self, text: str, max_length: int = 150, min_length: int = 50) -> Tuple[str, Dict]:
        """
        Generate a fluent summary using Groq Llama3.
        Falls back to extractive if GROQ_API_KEY is not set.
        """
        client = _get_groq()

        if client:
            try:
                excerpt      = text[:12000]
                target_words = max(min_length, min(max_length, 300))
                prompt = f"""You are an academic summarization assistant.

Write a fluent, well-structured summary of the text below in approximately {target_words} words.
- Use your own words — do NOT copy sentences verbatim.
- Capture the key ideas, arguments, and conclusions.
- Write in clear academic English.

Text:
{excerpt}

Summary:"""
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=512,
                )
                summary = response.choices[0].message.content.strip()
                return summary, {
                    "method":       "abstractive",
                    "engine":       "Groq Llama3",
                    "target_words": target_words,
                }
            except Exception as e:
                print(f"Groq abstractive summarization failed, falling back to extractive: {e}")

        # Fallback — extractive with more sentences
        return self.extractive_summarization(text, num_sentences=5)

    # ── Unified entry point ───────────────────────────────────────────────────

    def summarize(self, text: str, method: str = "extractive", **kwargs) -> Tuple[str, Dict]:
        if not text or len(text.strip()) < 50:
            raise ValueError("Text is too short (minimum 50 characters).")
        text = text.strip()
        if method == "extractive":
            return self.extractive_summarization(text, kwargs.get('num_sentences', 3))
        elif method == "abstractive":
            return self.abstractive_summarization(
                text, kwargs.get('max_length', 150), kwargs.get('min_length', 50))
        else:
            raise ValueError(f"Unknown method '{method}'. Use 'extractive' or 'abstractive'.")


# ── Standalone helpers ────────────────────────────────────────────────────────

def get_summary_stats(text: str, summary: str) -> Dict:
    ow = len(word_tokenize(text))
    sw = len(word_tokenize(summary))
    return {
        "original_words": ow,
        "summary_words":  sw,
        "original_chars": len(text),
        "summary_chars":  len(summary),
        "word_reduction": f"{(1 - sw/max(ow,1))*100:.1f}%",
        "char_reduction": f"{(1 - len(summary)/max(len(text),1))*100:.1f}%",
    }


def validate_text_length(text: str, min_length: int = 100) -> Tuple[bool, str]:
    if not text or len(text.strip()) < min_length:
        return False, f"Text is too short (minimum {min_length} characters)."
    if len(sent_tokenize(text)) < 2:
        return False, "Text needs at least 2 sentences."
    return True, ""