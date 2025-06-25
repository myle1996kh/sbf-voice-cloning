import speech_recognition as sr
import requests
import json
import tempfile
import os
from pydub import AudioSegment
import io

def process_speech_to_text(audio_file_path):
    """
    Convert audio file to text using Google Speech Recognition.
    
    Args:
        audio_file_path (str): Path to the audio file (wav format)
    
    Returns:
        str: Transcribed text or None if failed
    """
    recognizer = sr.Recognizer()
    
    try:
        # Convert to wav if needed and ensure proper format
        audio = AudioSegment.from_file(audio_file_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        
        # Create temporary wav file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            audio.export(temp_wav.name, format="wav")
            temp_wav_path = temp_wav.name
        
        # Perform speech recognition
        with sr.AudioFile(temp_wav_path) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            # Record the audio
            audio_data = recognizer.record(source)
        
        # Try Google Speech Recognition first
        try:
            text = recognizer.recognize_google(audio_data, language='en-US')
            return text
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            # Fallback to offline recognition if available
            try:
                text = recognizer.recognize_sphinx(audio_data)
                return text
            except:
                return None
    
    except Exception as e:
        print(f"Error in speech-to-text conversion: {e}")
        return None
    
    finally:
        # Clean up temporary file
        try:
            if 'temp_wav_path' in locals():
                os.unlink(temp_wav_path)
        except:
            pass

def correct_grammar_with_gintler(text):
    """
    Grammar correction using LanguageTool API (renamed from gintler for compatibility).
    LanguageTool is free, accurate, and supports 30+ languages.
    
    Args:
        text (str): Original text to be corrected
    
    Returns:
        str: Grammar-corrected text
    """
    return correct_grammar_with_languagetool(text)

def correct_grammar_with_languagetool(text):
    """
    Correct grammar using LanguageTool API.
    LanguageTool is a powerful, free grammar checker with excellent accuracy.
    
    Args:
        text (str): Original text
    
    Returns:
        str: Grammar-corrected text
    """
    
    print(f"🔍 DEBUG: Input text: '{text}'")
    
    try:
        # LanguageTool public API (free tier)
        url = "https://api.languagetool.org/v2/check"
        
        data = {
            'text': text,
            'language': 'en-US',
            'enabledOnly': 'false',  # Enable all rules
            'level': 'picky'  # More thorough checking
        }
        
        print("🌐 DEBUG: Calling LanguageTool API...")
        response = requests.post(url, data=data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            matches = result.get('matches', [])
            
            print(f"✅ DEBUG: LanguageTool found {len(matches)} issues")
            
            if not matches:
                print("ℹ️ DEBUG: No corrections needed")
                return text  # No corrections needed
            
            # Show what was found
            for i, match in enumerate(matches[:3]):  # Show first 3
                print(f"🔧 DEBUG Issue {i+1}: {match.get('message', 'No message')}")
                if match.get('replacements'):
                    print(f"   Suggestion: '{match['replacements'][0]['value']}'")
            
            # Apply corrections from end to beginning to preserve indices
            corrected_text = text
            corrections_made = 0
            
            for match in reversed(matches):
                if match.get('replacements') and len(match['replacements']) > 0:
                    start = match['offset']
                    length = match['length']
                    replacement = match['replacements'][0]['value']
                    
                    print(f"🔄 DEBUG: Replacing '{text[start:start+length]}' with '{replacement}'")
                    
                    # Apply the correction
                    corrected_text = corrected_text[:start] + replacement + corrected_text[start + length:]
                    corrections_made += 1
            
            print(f"✅ DEBUG: Applied {corrections_made} corrections")
            print(f"📝 DEBUG: Final result: '{corrected_text}'")
            return corrected_text
        else:
            print(f"❌ DEBUG: LanguageTool API error: {response.status_code}")
            return enhanced_grammar_correction(text)  # Fallback
            
    except requests.exceptions.Timeout:
        print("⏱️ DEBUG: LanguageTool API timeout - using fallback")
        return enhanced_grammar_correction(text)
    except Exception as e:
        print(f"💥 DEBUG: LanguageTool API error: {e}")
        return enhanced_grammar_correction(text)

def enhanced_grammar_correction(text):
    """
    Enhanced grammar corrections with better context awareness.
    Used as fallback when LanguageTool is unavailable.
    
    Args:
        text (str): Original text
    
    Returns:
        str: Text with corrections applied
    """
    
    if not text:
        return text
    
    # Convert to sentence for processing
    original_text = text.strip()
    words = original_text.split()
    corrected_words = []
    
    for i, word in enumerate(words):
        # Handle subject-verb agreement
        if i > 0:
            prev_word = words[i-1].lower().rstrip('.,!?')
            current_word = word.lower().rstrip('.,!?')
            
            # Subject-verb agreement fixes
            if prev_word in ['she', 'he', 'it'] and current_word == "don't":
                # Preserve punctuation
                punctuation = ''.join(c for c in word if c in '.,!?')
                corrected_words.append("doesn't" + punctuation)
                continue
            elif prev_word == 'i' and current_word == "doesn't":
                punctuation = ''.join(c for c in word if c in '.,!?')
                corrected_words.append("don't" + punctuation)
                continue
            elif prev_word in ['they', 'we', 'you'] and current_word == "doesn't":
                punctuation = ''.join(c for c in word if c in '.,!?')
                corrected_words.append("don't" + punctuation)
                continue
        
        # Basic word corrections
        word_clean = word.lower().rstrip('.,!?')
        punctuation = ''.join(c for c in word if c in '.,!?')
        
        corrections = {
            "im": "I'm",
            "cant": "can't", 
            "wont": "won't",
            "shouldnt": "shouldn't",
            "couldnt": "couldn't", 
            "wouldnt": "wouldn't",
            "isnt": "isn't",
            "arent": "aren't",
            "wasnt": "wasn't",
            "werent": "weren't",
            "hasnt": "hasn't",
            "havent": "haven't",
            "hadnt": "hadn't",
            "didnt": "didn't",
            "doesnt": "doesn't",
            "thats": "that's",
            "whats": "what's",
            "hes": "he's",
            "shes": "she's",
            "its": "it's",  # Only for "it is", not possessive
            "youre": "you're",
            "were": "we're",  # Context dependent
            "theyre": "they're"
        }
        
        # Apply basic corrections
        if word_clean in corrections:
            corrected_word = corrections[word_clean] + punctuation
        else:
            corrected_word = word
        
        corrected_words.append(corrected_word)
    
    # Rejoin text
    corrected_text = ' '.join(corrected_words)
    
    # Capitalize first letter
    if corrected_text:
        corrected_text = corrected_text[0].upper() + corrected_text[1:]
    
    # Ensure proper ending punctuation
    if corrected_text and not corrected_text.endswith(('.', '!', '?')):
        corrected_text += '.'
    
    # Clean up extra spaces
    corrected_text = ' '.join(corrected_text.split())
    
    return corrected_text

def get_grammar_correction_info():
    """
    Get information about the grammar correction system.
    """
    return {
        "primary_engine": "LanguageTool",
        "features": [
            "30+ languages support",
            "Free tier available", 
            "Advanced grammar rules",
            "Subject-verb agreement",
            "Punctuation correction",
            "Style suggestions"
        ],
        "fallback": "Enhanced rule-based correction",
        "api_endpoint": "https://api.languagetool.org/v2/check",
        "no_api_key_required": True,
        "accuracy": "High - 4.8/5 stars with 1M+ users"
    }

# Backward compatibility - keep existing function name
def basic_grammar_correction(text):
    """Backward compatibility wrapper."""
    return enhanced_grammar_correction(text)