import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import string
import tempfile  # Import tempfile module

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

def basic_grammar_fix(text):
    """Fix basic grammar issues in text"""
    if not text or not text.strip():
        return ""
    
    # Remove extra whitespaces
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Fix common contractions
    contractions = {
        r"\bi'm\b": "I'm",
        r"\byou're\b": "you're", 
        r"\bhe's\b": "he's",
        r"\bshe's\b": "she's",
        r"\bit's\b": "it's",
        r"\bwe're\b": "we're",
        r"\bthey're\b": "they're",
        r"\bcan't\b": "can't",
        r"\bwon't\b": "won't",
        r"\bdon't\b": "don't",
        r"\bdoesn't\b": "doesn't",
        r"\bisn't\b": "isn't",
        r"\baren't\b": "aren't",
        r"\bwasn't\b": "wasn't",
        r"\bweren't\b": "weren't",
        r"\bhadn't\b": "hadn't",
        r"\bhasn't\b": "hasn't",
        r"\bhaven't\b": "haven't"
    }
    
    for pattern, replacement in contractions.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Fix "i" to "I"
    text = re.sub(r'\bi\b', 'I', text)
    
    return text

def add_punctuation(text):
    """Add basic punctuation to text"""
    if not text or not text.strip():
        return ""
    
    # Remove existing punctuation at the end
    text = text.strip().rstrip(string.punctuation)
    
    # Split into sentences using basic patterns
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # If no sentence splitting occurred, treat as one sentence
    if len(sentences) == 1:
        # Add period if doesn't end with punctuation
        if not text.endswith(('.', '!', '?')):
            text += '.'
        return text
    
    # Process each sentence
    processed_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            # Add period if doesn't end with punctuation
            if not sentence.endswith(('.', '!', '?')):
                sentence += '.'
            processed_sentences.append(sentence)
    
    return ' '.join(processed_sentences)

def capitalize_sentences(text):
    """Capitalize first letter of each sentence"""
    if not text or not text.strip():
        return ""
    
    # Split into sentences
    sentences = sent_tokenize(text)
    
    capitalized_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            # Capitalize first letter
            sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
            capitalized_sentences.append(sentence)
    
    return ' '.join(capitalized_sentences)

def fix_common_speech_errors(text):
    """Fix common speech-to-text errors"""
    if not text or not text.strip():
        return ""
    
    # Common STT corrections
    corrections = {
        r'\bum+\b': '',  # Remove filler words
        r'\buh+\b': '',
        r'\ber+\b': '',
        r'\blike\s+like\b': 'like',  # Remove repeated words
        r'\band\s+and\b': 'and',
        r'\bthe\s+the\b': 'the',
        r'\ba\s+a\b': 'a',
        r'\bso\s+so\b': 'so',
        r'\byou\s+know\b': '',  # Remove filler phrases
        r'\bi\s+mean\b': '',
    }
    
    for pattern, replacement in corrections.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text.strip())
    
    return text

def clean_transcript(text):
    """Main function to clean and fix transcript text"""
    if not text or not text.strip():
        return ""
    
    # Step 1: Fix common speech errors
    text = fix_common_speech_errors(text)
    
    # Step 2: Basic grammar fixes
    text = basic_grammar_fix(text)
    
    # Step 3: Add punctuation
    text = add_punctuation(text)
    
    # Step 4: Capitalize sentences
    text = capitalize_sentences(text)
    
    # Final cleanup
    text = text.strip()
    
    return text

def transcribe_audio(model, audio_data):
    """Transcribe audio data to text using the specified model"""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        if isinstance(audio_data, bytes):
            tmp_file.write(audio_data)
        else:
            tmp_file.write(audio_data.read())
        tmp_path = tmp_file.name

    # Make sure the file is closed before using it
    result = model.transcribe(tmp_path, language="en", task="transcribe")
    
    return result