import sqlite3
import os
from datetime import datetime

DB_PATH = "voice_data.db"

def init_mirror_talk_db():
    """Initialize the Mirror Talk database table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mirror_talk_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT,
            voice_id TEXT NOT NULL,
            voice_name TEXT,
            original_text TEXT,
            corrected_text TEXT,
            emotion TEXT,
            pitch INTEGER,
            rate INTEGER,
            volume TEXT,
            original_audio_path TEXT,
            generated_audio_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_mirror_talk_session(session_name, voice_id, voice_name, original_text, 
                            corrected_text, emotion, pitch, rate, volume, 
                            original_audio_path, generated_audio_path):
    """Save a Mirror Talk session to database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO mirror_talk_sessions 
        (session_name, voice_id, voice_name, original_text, corrected_text, 
         emotion, pitch, rate, volume, original_audio_path, generated_audio_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (session_name, voice_id, voice_name, original_text, corrected_text, 
          emotion, pitch, rate, volume, original_audio_path, generated_audio_path))
    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return session_id

def load_all_mirror_talk_sessions():
    """Load all Mirror Talk sessions from database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, session_name, voice_name, original_text, corrected_text, 
               emotion, pitch, rate, volume, original_audio_path, 
               generated_audio_path, created_at
        FROM mirror_talk_sessions 
        ORDER BY created_at DESC
    """)
    sessions = cursor.fetchall()
    conn.close()
    return sessions

def get_mirror_talk_session_by_id(session_id):
    """Get a specific Mirror Talk session by ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM mirror_talk_sessions WHERE id = ?
    """, (session_id,))
    session = cursor.fetchone()
    conn.close()
    return session

def delete_mirror_talk_session(session_id):
    """Delete a Mirror Talk session and its associated files."""
    # Get session data first
    session = get_mirror_talk_session_by_id(session_id)
    if not session:
        return False
    
    # Delete files if they exist
    original_audio_path = session[10]  # original_audio_path column
    generated_audio_path = session[11]  # generated_audio_path column
    
    try:
        if original_audio_path and os.path.exists(original_audio_path):
            os.remove(original_audio_path)
        if generated_audio_path and os.path.exists(generated_audio_path):
            os.remove(generated_audio_path)
    except Exception as e:
        print(f"Error deleting files: {e}")
    
    # Delete database record
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM mirror_talk_sessions WHERE id = ?", (session_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

def get_mirror_talk_stats():
    """Get statistics about Mirror Talk usage."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total sessions
    cursor.execute("SELECT COUNT(*) FROM mirror_talk_sessions")
    total_sessions = cursor.fetchone()[0]
    
    # Most used voice
    cursor.execute("""
        SELECT voice_name, COUNT(*) as usage_count 
        FROM mirror_talk_sessions 
        GROUP BY voice_name 
        ORDER BY usage_count DESC 
        LIMIT 1
    """)
    most_used_voice = cursor.fetchone()
    
    # Most used emotion
    cursor.execute("""
        SELECT emotion, COUNT(*) as usage_count 
        FROM mirror_talk_sessions 
        GROUP BY emotion 
        ORDER BY usage_count DESC 
        LIMIT 1
    """)
    most_used_emotion = cursor.fetchone()
    
    # Sessions today
    cursor.execute("""
        SELECT COUNT(*) FROM mirror_talk_sessions 
        WHERE DATE(created_at) = DATE('now')
    """)
    sessions_today = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_sessions': total_sessions,
        'most_used_voice': most_used_voice,
        'most_used_emotion': most_used_emotion,
        'sessions_today': sessions_today
    }