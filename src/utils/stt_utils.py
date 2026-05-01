"""
Speech-to-Text Utilities for NoteGenie (Direct FFmpeg version)
"""
import speech_recognition as sr
import tempfile
import os
from pathlib import Path
from typing import Tuple, Dict
import subprocess

# Import from your config
try:
    from src.config import UPLOAD_DIR, ALLOWED_AUDIO_EXTENSIONS, MAX_AUDIO_SIZE
except ImportError:
    # Fallback if config import fails
    BASE_DIR = Path(__file__).parent.parent.parent
    UPLOAD_DIR = BASE_DIR / "uploads"
    UPLOAD_DIR.mkdir(exist_ok=True)
    ALLOWED_AUDIO_EXTENSIONS = {'.wav', '.mp3', '.m4a', '.ogg'}
    MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50MB

def get_ffmpeg_path() -> str:
    """Find FFmpeg executable - USING YOUR EXACT PATH"""
    # Your FFmpeg path
    ffmpeg_paths = [
        r'C:\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe',  # Your exact path
        'ffmpeg',  # Try if it's in PATH
        'C:\\ffmpeg\\bin\\ffmpeg.exe',
    ]
    
    for path in ffmpeg_paths:
        try:
            # Test if this path works
            result = subprocess.run(
                [path, '-version'],
                capture_output=True,
                text=True,
                shell=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✅ Found FFmpeg at: {path}")
                return path
        except subprocess.TimeoutExpired:
            print(f"⚠️  Timeout checking: {path}")
            continue
        except Exception as e:
            print(f"⚠️  Path {path} failed: {e}")
            continue
    
    print("❌ FFmpeg not found in any location")
    return None

def convert_with_ffmpeg_direct(input_path: str) -> str:
    """
    Convert any audio to WAV using FFmpeg directly
    """
    print(f"Converting {input_path} to WAV using FFmpeg...")
    
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        raise Exception("FFmpeg not found. Please install FFmpeg and add to PATH.")
    
    # Create temp WAV file
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    wav_path = temp_file.name
    temp_file.close()
    
    try:
        # FFmpeg command: convert to 16kHz mono WAV (best for speech recognition)
        cmd = [
            ffmpeg_path,
            '-i', input_path,           # Input file
            '-ar', '16000',             # Sample rate: 16kHz
            '-ac', '1',                 # Channels: 1 (mono)
            '-acodec', 'pcm_s16le',     # Codec: 16-bit PCM
            '-loglevel', 'error',       # Only show errors
            '-y',                       # Overwrite output
            wav_path                    # Output file
        ]
        
        print(f"Running FFmpeg: {' '.join(cmd)}")
        
        # Run FFmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=True,  # Important for Windows
            timeout=30   # 30 second timeout
        )
        
        if result.returncode != 0:
            print(f"FFmpeg stderr: {result.stderr}")
            raise Exception(f"FFmpeg conversion failed. Return code: {result.returncode}")
        
        # Verify file was created
        if not os.path.exists(wav_path):
            raise Exception("FFmpeg didn't create output file")
        
        file_size = os.path.getsize(wav_path)
        print(f"✅ Conversion successful!")
        print(f"   Output: {wav_path}")
        print(f"   Size: {file_size} bytes")
        
        return wav_path
        
    except subprocess.TimeoutExpired:
        print("❌ FFmpeg conversion timed out (30 seconds)")
        raise Exception("FFmpeg conversion timed out")
    except Exception as e:
        # Clean up temp file if creation failed
        if os.path.exists(wav_path):
            os.unlink(wav_path)
        print(f"❌ Conversion failed: {e}")
        raise e

def speech_to_text(audio_path: str, language: str = 'en-US') -> Tuple[bool, str, Dict]:
    """
    Convert speech audio to text using Google Speech Recognition
    """
    recognizer = sr.Recognizer()
    temp_wav_path = None
    
    try:
        print(f"=== STT START ===")
        print(f"Processing: {audio_path}")
        print(f"Language: {language}")
        print(f"File exists: {os.path.exists(audio_path)}")
        
        if os.path.exists(audio_path):
            print(f"File size: {os.path.getsize(audio_path)} bytes")
        
        # Check file size
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            if file_size > MAX_AUDIO_SIZE:
                return False, f"File too large. Maximum {MAX_AUDIO_SIZE // (1024*1024)}MB allowed.", {}
        
        # Convert to WAV if needed
        original_ext = Path(audio_path).suffix.lower()
        if original_ext != '.wav':
            print(f"Converting {original_ext} to WAV...")
            temp_wav_path = convert_with_ffmpeg_direct(audio_path)
            audio_to_process = temp_wav_path
            print(f"Using converted file: {audio_to_process}")
        else:
            audio_to_process = audio_path
            print("File is already WAV, no conversion needed")
        
        # Load and process audio
        print(f"Loading audio into speech_recognition...")
        with sr.AudioFile(audio_to_process) as source:
            # Get audio duration
            duration = source.DURATION
            print(f"Audio duration: {duration:.2f} seconds")
            
            # Adjust for ambient noise
            print("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            # Record the audio
            print("Recording audio...")
            audio_data = recognizer.record(source)
            
            # Recognize speech
            print("Recognizing speech with Google API...")
            text = recognizer.recognize_google(audio_data, language=language)
            
            print(f"=== STT SUCCESS ===")
            print(f"Transcribed {len(text)} characters")
            print(f"First 100 chars: {text[:100]}...")
            
            result_data = {
                "characters": len(text),
                "words": len(text.split()),
                "language": language,
                "duration": f"{duration:.2f}s",
                "original_format": original_ext
            }
            
            return True, text, result_data
            
    except sr.UnknownValueError:
        error_msg = "Google Speech Recognition could not understand the audio"
        print(f"=== STT ERROR ===")
        print(error_msg)
        return False, error_msg, {}
        
    except sr.RequestError as e:
        error_msg = f"Could not request results from Google Speech Recognition service: {e}"
        print(f"=== STT ERROR ===")
        print(error_msg)
        return False, error_msg, {}
        
    except Exception as e:
        error_msg = f"Error in speech recognition: {str(e)}"
        print(f"=== STT ERROR ===")
        print(error_msg)
        import traceback
        traceback.print_exc()
        return False, error_msg, {}
        
    finally:
        # Clean up temp WAV file if created
        if temp_wav_path and os.path.exists(temp_wav_path):
            print(f"Cleaning up temp file: {temp_wav_path}")
            try:
                os.unlink(temp_wav_path)
            except:
                pass

# Keep other functions the same
def get_supported_languages() -> Dict[str, str]:
    """Get supported languages for STT"""
    languages = {
        'en-US': 'English (US)',
        'en-GB': 'English (UK)',
        'es-ES': 'Spanish (Spain)',
        'fr-FR': 'French',
        'de-DE': 'German',
        'it-IT': 'Italian',
        'pt-PT': 'Portuguese',
        'hi-IN': 'Hindi',
        'ta-IN': 'Tamil',
        'te-IN': 'Telugu',
        'kn-IN': 'Kannada',
        'ml-IN': 'Malayalam',
        'ja-JP': 'Japanese',
        'ko-KR': 'Korean',
        'zh-CN': 'Chinese (Simplified)',
        'zh-TW': 'Chinese (Traditional)',
        'ru-RU': 'Russian',
        'ar-SA': 'Arabic'
    }
    return languages

def validate_audio_file(filename: str) -> Tuple[bool, str]:
    """Validate audio file"""
    if not any(filename.lower().endswith(ext) for ext in ALLOWED_AUDIO_EXTENSIONS):
        return False, f"Unsupported audio format. Allowed: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}"
    
    return True, ""