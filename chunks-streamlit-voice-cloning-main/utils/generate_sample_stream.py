import os
import requests
import xml.sax.saxutils as xml_escape

def generate_sample_stream(text, voice_id, ssml_params):
    """
    Tạo audio stream với các tham số SSML sử dụng Speechify Streaming API.
    """
    API_KEY = os.getenv("SPEECHIFY_API_KEY")

    ssml_text = f"""
    <speak>
        <prosody rate="{ssml_params['rate']}" pitch="{ssml_params['pitch']}" volume="{ssml_params['volume']}">
            <emotion category="{ssml_params['emotion']}" intensity="{ssml_params['intensity']}">
                {xml_escape.escape(text)}
            </emotion>
        </prosody>
    </speak>
    """

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "ssml": ssml_text,
        "voice_id": voice_id,
        "output_format": "mp3"
    }

    response = requests.post("https://api.sws.speechify.com/v1/audio/stream", headers=headers, json=payload)
    response.raise_for_status()

    return response.content  # MP3 bytes
