class MediaBriefError(Exception):
    """Base exception for our application."""
    pass

class FileProcessingError(MediaBriefError):
    """Raised when file loading or OCR fails."""
    pass

class LLMGenerationError(MediaBriefError):
    """Raised when Ollama fails to respond correctly."""
    pass