import os
import asyncio
import logging
import hashlib
from django.core.cache import cache
from pypdf import PdfReader
from pptx import Presentation
import google.generativeai as genai
import edge_tts

logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
# Configure the standard Gemini library
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    logger.warning("GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=api_key)

# Initialize the model (Standard 1.5 Flash is best for large context)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- HELPERS ---

def get_stable_hash(text):
    """
    Creates a consistent hash of text for caching.
    Python's built-in hash() is random per session (salt), which breaks caching 
    across server restarts.
    """
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

# --- FILE EXTRACTION ---

def extract_text_from_file(file_path):
    """
    Standard text extraction for PDF, PPTX, and TXT.
    Returns stripped text or empty string on error.
    """
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    
    try:
        if ext == '.pdf':
            reader = PdfReader(file_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        elif ext in ['.pptx', '.ppt']:
            prs = Presentation(file_path)
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"
        
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")
        return ""

# --- AI GENERATION ---

def get_ai_response(document_text, user_question, language='en', document_title=""):
    """
    Get AI response using standard google.generativeai library.
    """
    # Create stable cache key
    text_hash = get_stable_hash(document_text[:1000]) # Hash first 1000 chars to identify doc
    q_hash = get_stable_hash(user_question)
    cache_key = f"ai_resp_{text_hash}_{q_hash}_{language}"
    
    # Check cache
    cached_response = cache.get(cache_key)
    if cached_response:
        logger.info("Returning cached AI response")
        return cached_response
    
    # Language mapping
    language_names = {
        'en': 'English', 'yo': 'Yoruba', 'sw': 'Swahili', 
        'ha': 'Hausa', 'zu': 'Zulu', 'ig': 'Igbo', 
        'fr': 'French', 'pt': 'Portuguese'
    }
    lang_name = language_names.get(language, 'English')
    
    # System Prompt (Context)
    # Gemini 1.5 Flash has a 1M token window, so we pass the full text.
    # We cap it at ~500k chars to be safe (approx 125k tokens), leaving plenty of room.
    safe_context = document_text[:500000]
    
    prompt = f"""
    You are an AI tutor for African students. Use the provided document to answer the question.
    
    Document Title: {document_title}
    
    Document Content:
    {safe_context}
    
    ---
    User Question: {user_question}
    ---
    
    Instructions:
    1. Answer primarily based on the document content.
    2. Be educational, encouraging, and clear.
    3. Use African context/examples where applicable.
    4. Respond in {lang_name}.
    """
    
    try:
        # Standard generation call
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1000,
            )
        )
        
        answer = response.text
        
        # Cache for 1 hour
        cache.set(cache_key, answer, 3600)
        return answer
        
    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        return "I encountered an error analyzing the document. Please try again."

def generate_document_insights(document_text, language='en'):
    """
    Generate summaries and quiz questions.
    """
    text_hash = get_stable_hash(document_text[:1000])
    cache_key = f"doc_insights_{text_hash}_{language}"
    
    cached_insights = cache.get(cache_key)
    if cached_insights:
        return cached_insights
    
    safe_context = document_text[:500000]
    
    prompt = f"""
    Analyze this document and provide a summary structure.
    
    Document Content:
    {safe_context}
    
    Task:
    1. Provide a 2-sentence summary.
    2. List 3 key topics.
    3. Suggest 2 study questions.
    
    Output Language: {language}
    """
    
    try:
        response = model.generate_content(prompt)
        insights = response.text
        cache.set(cache_key, insights, 7200) # Cache for 2 hours
        return insights
    except Exception as e:
        logger.error(f"Insights Error: {e}")
        return "Insights unavailable."

def generate_quiz_questions(document_text, num_questions=3):
    """
    Generate multiple choice questions.
    """
    safe_context = document_text[:500000]
    
    prompt = f"""
    Create {num_questions} multiple-choice questions based on this text.
    Format:
    Q: [Question]
    A) [Option] ...
    Correct: [Answer]
    
    Text:
    {safe_context}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Quiz Error: {e}")
        return "Quiz generation failed."

# --- AUDIO GENERATION ---

async def _generate_audio_async(text, output_path, language="English"):
    """
    Internal async function for TTS.
    """
    voice_map = {
        "English": "en-NG-AbeoNeural",
        "Swahili": "sw-KE-RafikiNeural",
        "Amharic": "am-ET-MekdesNeural",
        "Hausa": "ha-NG-DanjumaNeural",
        "Igbo": "ig-NG-EzinneNeural",
        "Yoruba": "yo-NG-BolajiNeural",
        "Zulu": "zu-ZA-ThandoNeural",
        "Afrikaans": "af-ZA-AdriNeural"
    }
    
    voice = voice_map.get(language, "en-NG-AbeoNeural")
    
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        return False

def run_tts_sync(text, output_path, language):
    """
    Wrapper to run async TTS in synchronous Django views.
    Creates a new event loop for the operation.
    """
    try:
        asyncio.run(_generate_audio_async(text, output_path, language))
    except Exception as e:
        logger.error(f"Sync TTS Wrapper Error: {e}")