from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import requests

def extract_video_id(url):
    parsed_url = urlparse(url)
    if "youtube" in parsed_url.netloc:
        return parse_qs(parsed_url.query).get("v", [None])[0]
    elif "youtu.be" in parsed_url.netloc:
        return parsed_url.path.lstrip("/")
    return None

def fetch_youtube_title(video_id):
    try:
        response = requests.get(f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json")
        if response.status_code == 200:
            return response.json().get("title", f"YouTube ({video_id})")
    except Exception as e:
        print("Error fetching title:", e)
    return f"YouTube ({video_id})"

def get_youtube_transcript(url):
    '''
    Extract video_id from YouTube URL and fetch transcript as plain text.
    Returns: (transcript_text, video_title)
    '''
    try:
        video_id = extract_video_id(url)
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([item['text'] for item in transcript_list])
        title = fetch_youtube_title(video_id)
        return transcript_text, title
    except Exception as e:
        print("Error getting YouTube transcript:", e)
        return None, None
