import os

# API Configuration
SPEECHIFY_API_KEY = "W1vp8RVy2tnAw0GEj0NPqRszlWIXCfiDyLR5qOsY1rw="

# Database Configuration
DB_PATH = "voice_data.db"

# File Paths
OUTPUT_DIR = "output"
ASSETS_DIR = "assets"

# Audio Configuration
SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.m4a', '.flac']
MAX_AUDIO_FILE_SIZE = 50 * 1024 * 1024  # 50MB
DEMO_AUDIO_CHAR_LIMIT = 200

# Speech Recognition Configuration
SPEECH_RECOGNITION_LANGUAGE = 'en-US'
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1

# Mirror Talk Configuration
MIRROR_TALK_PREFIX = "mirror_"
ORIGINAL_AUDIO_PREFIX = "mirror_original_"
GENERATED_AUDIO_PREFIX = "mirror_generated_"

# NLP Configuration
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/prithivida/grammar_error_correcter_v1"
LANGUAGETOOL_API_URL = "https://api.languagetool.org/v2/check"

# UI Configuration
FILES_PER_ROW = 3
MAX_RECENT_SESSIONS = 5
DEFAULT_EMOTION_INDEX = 7  # "calm"
DEFAULT_VOLUME_INDEX = 2   # "medium"

# File naming patterns
def get_timestamp():
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def get_mirror_session_name(timestamp=None):
    if not timestamp:
        timestamp = get_timestamp()
    return f"Mirror Talk {timestamp}"

def get_original_audio_path(timestamp=None):
    if not timestamp:
        timestamp = get_timestamp()
    return os.path.join(OUTPUT_DIR, f"{ORIGINAL_AUDIO_PREFIX}{timestamp}.wav")

def get_generated_audio_path(timestamp=None):
    if not timestamp:
        timestamp = get_timestamp()
    return os.path.join(OUTPUT_DIR, f"{GENERATED_AUDIO_PREFIX}{timestamp}.mp3")

# Ensure output directory exists
def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# Validation functions
def is_supported_audio_format(filename):
    return any(filename.lower().endswith(fmt) for fmt in SUPPORTED_AUDIO_FORMATS)

def is_file_size_valid(file_path):
    try:
        return os.path.getsize(file_path) <= MAX_AUDIO_FILE_SIZE
    except:
        return False