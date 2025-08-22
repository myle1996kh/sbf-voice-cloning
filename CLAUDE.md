# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## Project Architecture

This is a Streamlit-based voice cloning application that uses the Speechify API for text-to-speech generation. The app has a multi-tab interface for different functionalities.

### Core Structure

- **app.py**: Main Streamlit application with navigation tabs:
  - Voice Setup: Configure and manage voice models
  - Transcript: YouTube transcript extraction and processing
  - Generate Podcast: Text-to-speech generation with customization
  - Mirror Talk: Audio recording, transcription, and voice synthesis
  - Manage Files: File management utilities

- **utils/**: Core functionality modules
  - `speechify_api.py`: Speechify API integration for voice generation
  - `voice_utils.py`: Voice management and SQLite database operations
  - `nlp_processor.py`: Speech-to-text processing and grammar correction
  - `mirror_talk_db.py`: Mirror Talk session database management
  - `transcript_db.py`: YouTube transcript database operations
  - `yt_utils.py`: YouTube video processing utilities
  - `text_processing.py`: Text manipulation utilities
  - `config.py`: Application configuration and constants

### Database Schema

Uses SQLite (`voice_data.db`) with tables:
- `voice_library`: Stores voice models and metadata
- `mirror_talk_sessions`: Stores Mirror Talk session data
- `transcript`: Stores YouTube transcript data

### Key Features

- Voice cloning with emotion, pitch, speed, and volume control
- Audio recording and transcription
- YouTube transcript extraction
- Grammar correction using external APIs
- File management for generated audio outputs

### API Configuration

The application uses a hardcoded Speechify API key in `config.py` and `app.py`. The key is visible in the codebase and should be moved to environment variables for security.

### Output Directory

Generated audio files are stored in `output/` with timestamped filenames using different prefixes:
- `mirror_original_*`: Original recorded audio
- `mirror_generated_*`: Generated voice cloning audio
- `demo_output_*`: Demo audio files