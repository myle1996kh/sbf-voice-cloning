import sqlite3
import os

DB_PATH = "voice_data.db"

def init_transcript_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            video_id TEXT,
            transcript TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_transcript(source, video_id, transcript):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transcripts (source, video_id, transcript)
        VALUES (?, ?, ?)
    """, (source, video_id, transcript))
    conn.commit()
    conn.close()

def load_all_transcripts():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, source, video_id, transcript FROM transcripts ORDER BY id DESC")
    data = cursor.fetchall()
    conn.close()
    return data

def get_transcript_by_id(transcript_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT transcript FROM transcripts WHERE id = ?", (transcript_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None
