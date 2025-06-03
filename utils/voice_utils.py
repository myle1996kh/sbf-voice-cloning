import os
import sqlite3
import requests

API_KEY = "W1vp8RVy2tnAw0GEj0NPqRszlWIXCfiDyLR5qOsY1rw="
DB_PATH = "voice_data.db"

def init_voice_db():
    """Initialize the SQLite DB with voice table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voice_library (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            voice_id TEXT NOT NULL,
            audio_path TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_voice_id(name, audio_file_path):
    """Upload audio to Speechify and get voice_id."""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    with open(audio_file_path, "rb") as f:
        files = {"sample": f}
        data = {
            "name": name,
            "consent": '{"fullName": "User", "email": "user@example.com"}'
        }
        response = requests.post(
            "https://api.sws.speechify.com/v1/voices",
            headers=headers, files=files, data=data
        )
    if response.status_code == 200:
        return response.json().get("id")
    return None

def save_voice_to_db(name, voice_id, audio_path):
    """Save voice_id into local SQLite DB."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO voice_library (name, voice_id, audio_path)
        VALUES (?, ?, ?)
    """, (name, voice_id, audio_path))
    conn.commit()
    conn.close()

def load_all_voice_ids():
    """Fetch all saved voice entries from DB."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, voice_id FROM voice_library")
    results = cursor.fetchall()
    conn.close()
    return results
