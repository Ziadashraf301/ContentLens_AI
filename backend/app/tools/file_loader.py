from pathlib import Path
from app.core.config import settings
from app.core.logging import logger
from .ocr import perform_ocr
from ..utils.file_utils import get_file_extension
from ..utils.text_utils import clean_extra_whitespace
from ..utils.exceptions import FileProcessingError

# Optional dependencies handled gracefully
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx
except ImportError:
    docx = None

class FileLoader:
    """
    Handles loading and extracting text from supported files.
    Refined to use project utilities and standardized cleaning.
    """

    SUPPORTED_EXTENSIONS = settings.ALLOWED_EXTENSIONS.split(",")

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.validate_file()

    def validate_file(self):
        if not self.file_path.exists():
            logger.error(f"File not found: {self.file_path}")
            raise FileNotFoundError(f"File not found: {self.file_path}")

        # Extension check
        ext = get_file_extension(self.file_path).replace(".", "")
        if ext not in self.SUPPORTED_EXTENSIONS:
            supported = settings.ALLOWED_EXTENSIONS
            logger.error(f"Unsupported file type: {ext}")
            raise ValueError(
                f"File type '.{ext}' is not supported. "
                f"Supported formats: {supported}"
            )

        # Size check
        if self.file_path.stat().st_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            logger.error(f"File too large: {self.file_path}")
            raise ValueError(f"File exceeds max size of {settings.MAX_FILE_SIZE_MB} MB")

    def load(self) -> str:
        """Main entry point for loading text."""
        try:
            ext = get_file_extension(self.file_path)
            
            # Use dict mapping
            loaders = {
                ".txt": self._load_txt,
                ".pdf": self._load_pdf,
                ".docx": self._load_docx,
                ".png": self._load_image,
                ".jpg": self._load_image,
                ".jpeg": self._load_image,
                ".gif": self._load_image,
            }

            loader  = loaders.get(ext)

            if not loader:
                raise ValueError(f"No loader found for extension: {ext}")
            
            text = loader()

            # Ensure the text is sanitized before it hits the agents
            return clean_extra_whitespace(text)

        except Exception as e:
            logger.error(f"FileLoader error on {self.file_path}: {e}")
            raise FileProcessingError(
                f"Failed to process file: {str(e)}"
            ) from e

    def _load_txt(self) -> str:
        logger.info(f"Loading TXT file: {self.file_path}")
        with open(self.file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _load_pdf(self) -> str:
        if not PyPDF2:
            raise ImportError("PyPDF2 is required to load PDF files")
        logger.info(f"Loading PDF file: {self.file_path}")
        text = ""
        with open(self.file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text

    def _load_docx(self) -> str:
        if not docx:
            raise ImportError("python-docx is required to load DOCX files")
        logger.info(f"Loading DOCX file: {self.file_path}")
        document = docx.Document(self.file_path)
        return "\n".join([para.text for para in document.paragraphs])

    def _load_image(self) -> str:
        # Delegate to specialized OCR tool
        logger.info(f"Handoff: Sending image to OCR tool: {self.file_path}")
        return perform_ocr(str(self.file_path))