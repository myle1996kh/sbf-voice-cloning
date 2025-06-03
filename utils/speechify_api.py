import requests
import os
import time

EMOTION_OPTIONS = [
    "angry", "cheerful", "sad", "terrified", "relaxed",
    "fearful", "surprised", "calm", "assertive", "energetic",
    "warm", "direct", "bright","none"
]

def fetch_voice_ids(api_key):
    """Fetch list of voice_ids from Speechify API."""
    url = "https://api.sws.speechify.com/v1/voices"
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        voices = response.json()
        return [
            (
                v.get("label") or
                v.get("name") or
                v.get("metadata", {}).get("label", "Unnamed Voice"),
                v.get("id")
            )
            for v in voices if v.get("id")
        ]
    else:
        print(f"Error fetching voices: {response.status_code} - {response.text}")
        return []

def generate_audio_with_params(api_key, voice_id, text, emotion,
                                pitch_pct, rate_pct, volume_level,
                                output_path=None):
    """Generate audio using SSML via /v1/audio/stream endpoint."""

    if output_path is None:
        timestamp = int(time.time() * 1000)
        output_path = f"output/output_{timestamp}.mp3"

    if emotion == "none":
        ssml_text = (
            f'<speak>'
            f'<prosody rate="{rate_pct:+d}%" pitch="{pitch_pct:+d}%" volume="{volume_level}">{text}</prosody>'
            f'</speak>'
        )
    else:
        ssml_text = (
            f'<speak>'
            f'<speechify:style emotion="{emotion}">' 
            f'<prosody rate="{rate_pct:+d}%" pitch="{pitch_pct:+d}%" volume="{volume_level}">{text}</prosody>'
            f'</speechify:style>'
            f'</speak>'
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "audio/mpeg",
        "Content-Type": "application/json"
    }

    payload = {
        "input": ssml_text,
        "voice_id": voice_id
    }

    url = "https://api.sws.speechify.com/v1/audio/stream"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        response = requests.post(url, headers=headers, json=payload, stream=True)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return output_path
        else:
            print("❌ API Error:", response.status_code, response.text)
            return None
    except Exception as e:
        print("❌ Exception during request:", e)
        return None

def generate_demo_audio(api_key, voice_id, full_text, emotion, pitch_pct, rate_pct, volume_level, output_path=None):
    """
    Generate demo audio with only the first 500 characters.
    """
    limited_text = full_text[:200]  # Limit to 200 characters
    if output_path is None:
        timestamp = int(time.time() * 1000)
        output_path = f"output/demo_output_{timestamp}.mp3"
    return generate_audio_with_params(
        api_key=api_key,
        voice_id=voice_id,
        text=limited_text,
        emotion=emotion,
        pitch_pct=pitch_pct,
        rate_pct=rate_pct,
        volume_level=volume_level,
        output_path=output_path
    )
