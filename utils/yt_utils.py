import re
import requests
from urllib.parse import urlparse, parse_qs
import time

def extract_video_id(url):
    """Extract video ID from various YouTube URL formats"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/watch\?.*v=([^&\n?#]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_youtube_transcript(url):
    """
    Get transcript from YouTube video using multiple methods
    Returns: (transcript_text, video_title)
    """
    video_id = extract_video_id(url)
    if not video_id:
        return None, "Invalid YouTube URL"
    
    # Method 1: Try youtube-transcript-api
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # Get available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to get English transcript first
        try:
            transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
            transcript_data = transcript.fetch()
        except:
            # If no English, get the first available transcript
            available_transcripts = list(transcript_list)
            if available_transcripts:
                transcript_data = available_transcripts[0].fetch()
            else:
                raise Exception("No transcripts available")
        
        # Extract text from transcript data
        transcript_text = ' '.join([item['text'] for item in transcript_data])
        
        # Get video title
        video_title = get_video_title(video_id)
        
        return transcript_text, video_title
        
    except Exception as e:
        print(f"Method 1 failed: {str(e)}")
        
        # Method 2: Try alternative approach with requests
        return get_transcript_alternative(video_id)

def get_video_title(video_id):
    """Get video title from YouTube"""
    try:
        # Try getting title from YouTube oEmbed API
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(oembed_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('title', f'YouTube Video {video_id}')
    except:
        pass
    
    return f"YouTube Video {video_id}"

def get_transcript_alternative(video_id):
    """Alternative method to get transcript"""
    try:
        # Method 2A: Try with different language codes
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # Extended list of language codes to try
        language_codes = [
            'en', 'en-US', 'en-GB', 'en-CA', 'en-AU',
            'vi', 'vi-VN',  # Vietnamese
            'auto',  # Auto-generated
            'a.en',  # Auto-generated English
            'a.vi',  # Auto-generated Vietnamese
        ]
        
        for lang_code in language_codes:
            try:
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang_code])
                transcript_text = ' '.join([item['text'] for item in transcript_data])
                video_title = get_video_title(video_id)
                return transcript_text, video_title
            except Exception as lang_error:
                print(f"Language {lang_code} failed: {lang_error}")
                continue
        
        # Method 2B: Try getting any available transcript
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        for transcript in transcript_list:
            try:
                transcript_data = transcript.fetch()
                transcript_text = ' '.join([item['text'] for item in transcript_data])
                video_title = get_video_title(video_id)
                return transcript_text, video_title
            except:
                continue
                
    except Exception as e:
        print(f"Alternative method failed: {str(e)}")
    
    # Method 3: Web scraping approach (fallback)
    return get_transcript_web_scraping(video_id)

def get_transcript_web_scraping(video_id):
    """Fallback method using web scraping"""
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # Get the YouTube video page
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # Try to extract title from page
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.find('title')
            video_title = title_tag.text.replace(' - YouTube', '') if title_tag else f"YouTube Video {video_id}"
            
            # Look for transcript data in the page
            # This is a simplified approach - you might need to look for specific patterns
            page_text = response.text
            
            # Try to find timedtext URLs in the page source
            timedtext_pattern = r'"timedtext".*?"baseUrl":"([^"]+)"'
            matches = re.findall(timedtext_pattern, page_text)
            
            if matches:
                # Try to get transcript from timedtext URL
                timedtext_url = matches[0].replace('\\u0026', '&')
                transcript_response = requests.get(timedtext_url, headers=headers, timeout=10)
                
                if transcript_response.status_code == 200:
                    # Parse the XML transcript
                    from xml.etree import ElementTree as ET
                    root = ET.fromstring(transcript_response.text)
                    transcript_texts = []
                    
                    for text_elem in root.findall('.//text'):
                        text_content = text_elem.text
                        if text_content:
                            transcript_texts.append(text_content.strip())
                    
                    if transcript_texts:
                        transcript_text = ' '.join(transcript_texts)
                        return transcript_text, video_title
            
            return None, "No transcript found using web scraping method"
        else:
            return None, f"Failed to access video page (Status: {response.status_code})"
            
    except Exception as e:
        return None, f"Web scraping failed: {str(e)}"

def test_transcript_methods(video_id):
    """Test all transcript methods for debugging"""
    print(f"Testing transcript methods for video: {video_id}")
    
    # Test Method 1
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        print(f"Available transcripts: {[t.language_code for t in transcript_list]}")
        
        for transcript in transcript_list:
            print(f"- Language: {transcript.language_code}, Generated: {transcript.is_generated}, Translatable: {transcript.is_translatable}")
            
    except Exception as e:
        print(f"Error listing transcripts: {e}")
    
    # Test getting transcript
    transcript_text, video_title = get_youtube_transcript(f"https://www.youtube.com/watch?v={video_id}")
    print(f"Result: {video_title}")
    print(f"Transcript length: {len(transcript_text) if transcript_text else 0}")
    
    return transcript_text, video_title

# Enhanced error handling for common issues
def handle_transcript_errors(error_message):
    """Provide specific error messages for common transcript issues"""
    error_lower = str(error_message).lower()
    
    if "no element found" in error_lower:
        return "The video's transcript data is corrupted or in an unsupported format"
    elif "transcript disabled" in error_lower:
        return "Transcripts have been disabled for this video by the creator"
    elif "no transcript" in error_lower:
        return "No transcripts are available for this video"
    elif "private" in error_lower:
        return "This video is private or restricted"
    elif "unavailable" in error_lower:
        return "This video is unavailable or has been removed"
    elif "forbidden" in error_lower:
        return "Access to this video's transcript is forbidden"
    else:
        return f"Transcript extraction failed: {error_message}"