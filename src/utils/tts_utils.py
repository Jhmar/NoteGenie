"""
Text-to-Speech Utilities for NoteGenie
"""
from gtts import gTTS
from pathlib import Path
from typing import Tuple, Dict
import hashlib
import time

# Import from your config
try:
    from src.config import UPLOAD_DIR
except ImportError:
    # Fallback if config import fails
    BASE_DIR = Path(__file__).parent.parent.parent
    UPLOAD_DIR = BASE_DIR / "uploads"
    UPLOAD_DIR.mkdir(exist_ok=True)

def text_to_speech(text: str, language: str = 'en', filename: str = None) -> Tuple[bool, str, str]:
    """
    Convert text to speech and save as MP3 file
    
    Args:
        text: Text to convert to speech
        language: Language code (default: 'en' for English)
        filename: Optional custom filename
        
    Returns:
        Tuple of (success, message, audio_filename)
    """
    try:
        print(f"=== TTS START ===")
        print(f"Text length: {len(text)}")
        print(f"Language: {language}")
        print(f"Filename: {filename}")
        
        # Validate input
        if not text or len(text.strip()) == 0:
            print("Error: No text provided")
            return False, "No text provided", ""
        
        # Clean and limit text
        text = text.strip()
        print(f"Text after strip: '{text[:50]}...'")
        
        if len(text) > 10000:  # Limit for safety
            text = text[:10000]
            print(f"Warning: Text truncated to 10000 characters")
        
        # Generate filename if not provided
        if not filename:
            # Create hash from first 200 chars for uniqueness
            text_sample = text[:200].encode('utf-8')
            text_hash = hashlib.md5(text_sample).hexdigest()[:8]
            timestamp = int(time.time())
            filename = f"speech_{text_hash}_{timestamp}.mp3"
        
        # Ensure filename ends with .mp3
        if not filename.endswith('.mp3'):
            filename += '.mp3'
        
        # Create output path
        output_path = UPLOAD_DIR / filename
        print(f"Output path: {output_path}")
        print(f"UPLOAD_DIR exists: {UPLOAD_DIR.exists()}")
        
        # Generate speech using gTTS
        print(f"Generating speech for {len(text)} characters...")
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(str(output_path))
        print(f"Audio saved to: {output_path}")
        
        # Verify file was created
        if output_path.exists():
            file_size = output_path.stat().st_size
            file_size_kb = file_size / 1024
            
            print(f"File created successfully!")
            print(f"File size: {file_size} bytes ({file_size_kb:.1f} KB)")
            
            if file_size > 0:
                return True, f"Audio generated ({file_size_kb:.1f} KB)", filename
            else:
                print("Error: File is empty")
                return False, "Generated audio file is empty", ""
        else:
            print("Error: File was not created")
            return False, "Failed to create audio file", ""
            
    except Exception as e:
        error_msg = f"Error generating speech: {str(e)}"
        print(f"=== TTS ERROR ===")
        print(error_msg)
        import traceback
        traceback.print_exc()
        print(f"=== END ERROR ===")
        return False, error_msg, ""

def get_available_languages() -> Dict[str, str]:
    """
    Return dictionary of available languages for TTS
    
    Returns:
        Dictionary with language codes as keys and language names as values
    """
    languages = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'ja': 'Japanese',
        'ko': 'Korean',
        'hi': 'Hindi',
        'ta': 'Tamil',
        'te': 'Telugu',
        'kn': 'Kannada',
        'ml': 'Malayalam',
        'zh-CN': 'Chinese (Simplified)',
        'zh-TW': 'Chinese (Traditional)',
        'ar': 'Arabic'
    }
    return languages

def delete_audio_file(filename: str) -> bool:
    """Delete audio file from uploads directory"""
    try:
        file_path = UPLOAD_DIR / filename
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    except:
        return False