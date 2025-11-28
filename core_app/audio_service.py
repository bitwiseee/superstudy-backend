from gtts import gTTS
import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


# Language mapping for gTTS (Google Text-to-Speech)
LANGUAGE_MAP = {
    'en': 'en',      # English
    'yo': 'yo',      # Yoruba (experimental support)
    'ig': 'ig',      # Igbo (limited support)
    'ha': 'ha',      # Hausa (experimental support)
}

# Languages with good gTTS support
SUPPORTED_AUDIO_LANGUAGES = ['en', 'yo', 'ha']


def is_audio_supported(language):
    """
    Check if audio generation is supported for a language
    
    Args:
        language: Language code
        
    Returns:
        bool: True if supported
    """
    return language in SUPPORTED_AUDIO_LANGUAGES


def generate_audio(text, language='en', filename=None, slow=False):
    """
    Generate audio file from text using gTTS
    
    Args:
        text: Text to convert to speech
        language: Language code
        filename: Optional custom filename
        slow: Whether to use slow speech
        
    Returns:
        str: Relative path to audio file, or None if failed
    """
    try:
        # Get language code for gTTS
        tts_lang = LANGUAGE_MAP.get(language, 'en')
        
        # Truncate text if too long (gTTS has limits)
        max_length = 5000  # characters
        if len(text) > max_length:
            text = text[:max_length] + "..."
            logger.warning(f"Text truncated to {max_length} characters for audio generation")
        
        # Check if language is supported
        if language not in SUPPORTED_AUDIO_LANGUAGES:
            logger.warning(f"Audio not well-supported for language: {language}, falling back to English")
            tts_lang = 'en'
        
        # Generate unique filename if not provided
        if not filename:
            filename = f"audio_{os.urandom(8).hex()}.mp3"
        
        # Ensure audio directory exists
        audio_dir = os.path.join(settings.MEDIA_ROOT, 'audio')
        os.makedirs(audio_dir, exist_ok=True)
        
        # Full file path
        filepath = os.path.join(audio_dir, filename)
        
        # Generate speech
        tts = gTTS(text=text, lang=tts_lang, slow=slow)
        tts.save(filepath)
        
        # Return relative path for URL generation
        relative_path = os.path.join('audio', filename)
        
        logger.info(f"Audio generated: {relative_path} (language: {tts_lang})")
        return relative_path
        
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        return None


def generate_audio_for_chat(chat_instance):
    """
    Generate audio for a Chat object and update its audio_path
    
    Args:
        chat_instance: Chat model instance
        
    Returns:
        str: Audio path or None if failed
    """
    if not chat_instance.answer:
        logger.warning("Cannot generate audio: No answer text")
        return None
    
    # Check if language is supported
    if not is_audio_supported(chat_instance.language):
        logger.info(f"Audio generation skipped for unsupported language: {chat_instance.language}")
        return None
    
    # Limit text length for audio
    text_to_speak = chat_instance.answer
    
    # Generate audio
    audio_path = generate_audio(
        text_to_speak,
        language=chat_instance.language,
        filename=f"chat_{chat_instance.id}.mp3"
    )
    
    if audio_path:
        chat_instance.audio_path = audio_path
        chat_instance.save()
        logger.info(f"Audio saved for chat {chat_instance.id}")
    
    return audio_path


def get_audio_url(audio_path, request=None):
    """
    Convert audio path to full URL
    
    Args:
        audio_path: Relative audio path
        request: Optional request object for building absolute URI
        
    Returns:
        str: Full audio URL or None
    """
    if not audio_path:
        return None
    
    if request:
        return request.build_absolute_uri(f"{settings.MEDIA_URL}{audio_path}")
    
    return f"{settings.MEDIA_URL}{audio_path}"


def delete_audio_file(audio_path):
    """
    Delete audio file from filesystem
    
    Args:
        audio_path: Relative path to audio file
        
    Returns:
        bool: True if deleted successfully
    """
    if not audio_path:
        return False
    
    try:
        full_path = os.path.join(settings.MEDIA_ROOT, audio_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            logger.info(f"Deleted audio file: {audio_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting audio file {audio_path}: {e}")
        return False


def cleanup_old_audio(days=7):
    """
    Clean up audio files older than specified days
    Should be called periodically (e.g., via cron job)
    
    Args:
        days: Number of days to keep files
        
    Returns:
        int: Number of files deleted
    """
    import time
    
    audio_dir = os.path.join(settings.MEDIA_ROOT, 'audio')
    
    if not os.path.exists(audio_dir):
        logger.info("Audio directory does not exist")
        return 0
    
    now = time.time()
    cutoff = now - (days * 86400)
    
    deleted_count = 0
    
    try:
        for filename in os.listdir(audio_dir):
            filepath = os.path.join(audio_dir, filename)
            
            if os.path.isfile(filepath):
                file_age = os.stat(filepath).st_mtime
                
                if file_age < cutoff:
                    try:
                        os.remove(filepath)
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Error deleting {filepath}: {e}")
        
        logger.info(f"Cleaned up {deleted_count} old audio files")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error during audio cleanup: {e}")
        return deleted_count


def generate_bulk_audio(texts, language='en', prefix='bulk'):
    """
    Generate audio for multiple texts at once
    
    Args:
        texts: List of text strings
        language: Language code
        prefix: Filename prefix
        
    Returns:
        list: List of audio paths
    """
    audio_paths = []
    
    for i, text in enumerate(texts):
        filename = f"{prefix}_{i}_{os.urandom(4).hex()}.mp3"
        audio_path = generate_audio(text, language, filename)
        audio_paths.append(audio_path)
    
    return audio_paths