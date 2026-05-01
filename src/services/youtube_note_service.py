"""
YouTube Note Generation Service
Uses YouTube Transcript API + Google Gemini for AI note generation
"""
import re
import os
import requests
from typing import List, Dict
from youtube_transcript_api import YouTubeTranscriptApi
# Exception classes differ between library versions — import defensively
try:
    from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled
except ImportError:
    try:
        from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
    except ImportError:
        NoTranscriptFound = Exception
        TranscriptsDisabled = Exception
from groq import Groq


# ── Configure Gemini ────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


class YouTubeNoteService:
    def __init__(self):
        print("🔄 Initialising YouTube Note Service...")

        self.gemini_available = bool(GROQ_API_KEY)
        if self.gemini_available:
            self.client = Groq(api_key=GROQ_API_KEY)
            print("✅ Gemini AI ready")
        else:
            self.model = None
            print("⚠️  GROQ_API_KEY not set – falling back to basic extraction")

    # ── URL / ID helpers ─────────────────────────────────────────────────────

    def extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from any URL format."""
        url = url.strip()
        patterns = [
            r'(?:youtube\.com\/watch\?v=)([\w-]+)',
            r'(?:youtu\.be\/)([\w-]+)',
            r'(?:youtube\.com\/embed\/)([\w-]+)',
            r'(?:youtube\.com\/shorts\/)([\w-]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ValueError("Invalid YouTube URL. Please paste a valid youtube.com or youtu.be link.")

    def get_video_metadata(self, video_id: str) -> Dict:
        """
        Fetch video title and channel name via YouTube oEmbed API (no API key needed).
        Falls back gracefully if the request fails.
        """
        try:
            oembed_url = (
                f"https://www.youtube.com/oembed"
                f"?url=https://www.youtube.com/watch?v={video_id}&format=json"
            )
            resp = requests.get(oembed_url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "title": data.get("title", f"Video {video_id}"),
                    "author": data.get("author_name", "YouTube Creator"),
                }
        except Exception:
            pass
        return {"title": f"Video {video_id}", "author": "YouTube Creator"}

    # ── Transcript ───────────────────────────────────────────────────────────

    def get_transcript(self, video_id: str):
        """
        Fetch transcript using the exact API of the installed version.
        Your version has only .fetch() and .list() as instance methods.
        Returns (transcript_data: list[dict], full_text: str).
        """
        # Must instantiate — fetch() and list() are instance methods, not static
        api = YouTubeTranscriptApi()

        # ── Try fetch() with English first, then any language ────────────────
        raw = None
        last_error = None

        for langs in (('en',), ('en-US', 'en-GB', 'en'), None):
            try:
                if langs is None:
                    # Get available languages via list() then fetch the first one
                    transcript_list = api.list(video_id)
                    available = list(transcript_list)
                    if not available:
                        raise RuntimeError("No transcripts available for this video.")
                    # Try to find English, otherwise take first available
                    transcript = None
                    for t in available:
                        if t.language_code.startswith("en"):
                            transcript = t
                            break
                    if transcript is None:
                        transcript = available[0]
                    raw = transcript.fetch()
                else:
                    raw = api.fetch(video_id, languages=langs)
                break  # success — stop trying
            except Exception as e:
                last_error = e
                continue

        if raw is None:
            raise RuntimeError(
                f"Could not fetch transcript. The video may have captions "
                f"disabled or be age-restricted. (Detail: {last_error})"
            )

        normalised = self._normalise(raw)
        full_text  = " ".join(e["text"] for e in normalised)
        return normalised, full_text

    def _normalise(self, raw) -> list:
        """Convert FetchedTranscript or list to consistent list[dict]."""
        result = []
        for entry in raw:
            if isinstance(entry, dict):
                result.append({
                    "text":     entry.get("text", ""),
                    "start":    entry.get("start", 0),
                    "duration": entry.get("duration", 0),
                })
            else:
                result.append({
                    "text":     getattr(entry, "text", str(entry)),
                    "start":    getattr(entry, "start", 0),
                    "duration": getattr(entry, "duration", 0),
                })
        return result

    # ── Text helpers ─────────────────────────────────────────────────────────

    def chunk_text(self, text: str, max_chars: int = 12_000) -> List[str]:
        """Split text into chunks without breaking words."""
        words = text.split()
        chunks, current, length = [], [], 0
        for word in words:
            length += len(word) + 1
            if length > max_chars:
                chunks.append(" ".join(current))
                current, length = [word], len(word)
            else:
                current.append(word)
        if current:
            chunks.append(" ".join(current))
        return chunks

    # ── AI generation (Gemini) ────────────────────────────────────────────

    def _gemini(self, prompt: str) -> str:
        """Send a prompt to Groq and return the text response."""
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()

    def generate_summary(self, text: str, title: str) -> str:
        """Generate a concise, well-structured summary."""
        if not self.gemini_available:
            return self._fallback_summary(text)

        # Use only first ~12 000 chars to stay within token limits
        excerpt = self.chunk_text(text)[0]
        prompt = f"""You are an academic note-taking assistant.

Summarise the following YouTube video transcript titled "{title}" in 4-6 clear sentences.
Focus on the main topic, key arguments, and conclusions.
Write in plain English suitable for a student.

Transcript:
{excerpt}

Summary:"""
        try:
            return self._gemini(prompt)
        except Exception as e:
            print(f"Gemini summary failed: {e}")
            return self._fallback_summary(text)

    def generate_key_points(self, text: str, title: str, num_points: int = 6) -> List[str]:
        """Extract key learning points as a bullet list."""
        if not self.gemini_available:
            return self._fallback_key_points(text, num_points)

        excerpt = self.chunk_text(text)[0]
        prompt = f"""You are an academic note-taking assistant.

From the YouTube video transcript titled "{title}", extract exactly {num_points} key points.
- Each point should be a complete, informative sentence.
- Cover the most important concepts, facts, or steps.
- Output ONLY the {num_points} points, one per line, without numbering or bullet symbols.

Transcript:
{excerpt}

Key points:"""
        try:
            raw = self._gemini(prompt)
            points = [line.strip("•-– ").strip() for line in raw.splitlines() if line.strip()]
            return points[:num_points]
        except Exception as e:
            print(f"Gemini key points failed: {e}")
            return self._fallback_key_points(text, num_points)

    def generate_questions(self, text: str, title: str, num_questions: int = 5) -> List[str]:
        """Generate study/comprehension questions."""
        if not self.gemini_available:
            return self._fallback_questions(text, num_questions)

        excerpt = self.chunk_text(text)[0]
        prompt = f"""You are an academic note-taking assistant.

Generate exactly {num_questions} study questions based on the YouTube video titled "{title}".
- Questions should test understanding of the core content.
- Mix factual, conceptual, and analytical questions.
- Output ONLY the questions, one per line, without numbering or bullet symbols.

Transcript:
{excerpt}

Questions:"""
        try:
            raw = self._gemini(prompt)
            questions = [line.strip("•-– ").strip() for line in raw.splitlines() if line.strip() and "?" in line]
            # If the model didn't include "?", take all non-empty lines
            if len(questions) < num_questions:
                questions = [line.strip("•-– ").strip() for line in raw.splitlines() if line.strip()]
            return questions[:num_questions]
        except Exception as e:
            print(f"Gemini questions failed: {e}")
            return self._fallback_questions(text, num_questions)

    def generate_sections(self, text: str, title: str) -> List[Dict]:
        """Break the transcript into topic sections with mini-summaries."""
        if not self.gemini_available:
            return []

        excerpt = self.chunk_text(text)[0]
        prompt = f"""You are an academic note-taking assistant.

Divide the YouTube video "{title}" into 3-5 topic sections.
For each section output exactly two lines:
  TITLE: <short section title>
  CONTENT: <2-3 sentence summary of that section>

Transcript:
{excerpt}

Sections:"""
        try:
            raw = self._gemini(prompt)
            sections = []
            current = {}
            for line in raw.splitlines():
                line = line.strip()
                if line.upper().startswith("TITLE:"):
                    if current:
                        sections.append(current)
                    current = {"title": line.split(":", 1)[1].strip(), "content": ""}
                elif line.upper().startswith("CONTENT:") and current:
                    current["content"] = line.split(":", 1)[1].strip()
            if current:
                sections.append(current)
            return sections if sections else []
        except Exception as e:
            print(f"Gemini sections failed: {e}")
            return []

    # ── Timestamps ───────────────────────────────────────────────────────────

    def extract_timestamps(self, transcript_data: list, num_timestamps: int = 8) -> List[Dict]:
        """Pick evenly-spaced timestamps from the transcript."""
        if not transcript_data:
            return []
        step = max(1, len(transcript_data) // num_timestamps)
        timestamps = []
        for i in range(0, len(transcript_data), step):
            entry = transcript_data[i]
            minutes = int(entry["start"] // 60)
            seconds = int(entry["start"] % 60)
            text = entry["text"]
            timestamps.append({
                "time": f"{minutes:02d}:{seconds:02d}",
                "text": text[:80] + ("..." if len(text) > 80 else ""),
            })
            if len(timestamps) >= num_timestamps:
                break
        return timestamps

    # ── Fallback helpers (no AI) ──────────────────────────────────────────

    def _fallback_summary(self, text: str) -> str:
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 40]
        return ". ".join(sentences[:5]) + "."

    def _fallback_key_points(self, text: str, n: int) -> List[str]:
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 40]
        ranked = sorted(sentences, key=lambda s: len(s.split()), reverse=True)
        seen, points = set(), []
        for s in ranked:
            if s not in seen:
                seen.add(s)
                points.append(s)
            if len(points) >= n:
                break
        return points

    def _fallback_questions(self, text: str, n: int) -> List[str]:
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 40][:n]
        return [f"What does the video explain about: {s[:60]}?" for s in sentences]

    # ── Main entry point ─────────────────────────────────────────────────────

    def process_video(self, url: str) -> Dict:
        """Process a YouTube URL and return structured notes."""
        # Step 1 – validate URL
        video_id = self.extract_video_id(url)
        print(f"✅ Video ID: {video_id}")

        # Step 2 – metadata (title, author)
        metadata = self.get_video_metadata(video_id)
        title = metadata["title"]
        author = metadata["author"]
        print(f"📹 Title: {title}")

        # Step 3 – transcript
        transcript_data, full_text = self.get_transcript(video_id)

        if not full_text.strip():
            return {
                "title": title,
                "author": author,
                "duration": 0,
                "overview": "No transcript text could be extracted for this video.",
                "key_points": [
                    "This video may not have captions available.",
                    "Try a video with CC / subtitles enabled.",
                    "You can also use the audio upload feature instead.",
                ],
                "sections": [],
                "questions": [],
                "timestamps": [],
            }

        duration = (
            transcript_data[-1]["start"] + transcript_data[-1].get("duration", 0)
            if transcript_data else 0
        )

        # Step 4 – AI generation
        print("📝 Generating summary...")
        summary = self.generate_summary(full_text, title)

        print("🔑 Extracting key points...")
        key_points = self.generate_key_points(full_text, title)

        print("❓ Generating questions...")
        questions = self.generate_questions(full_text, title)

        print("📚 Building sections...")
        sections = self.generate_sections(full_text, title)

        print("⏱️  Extracting timestamps...")
        timestamps = self.extract_timestamps(transcript_data)

        print("✅ Notes generated successfully")
        return {
            "title": title,
            "author": author,
            "duration": round(duration),
            "overview": summary,
            "key_points": key_points,
            "sections": sections,
            "questions": questions,
            "timestamps": timestamps,
        }