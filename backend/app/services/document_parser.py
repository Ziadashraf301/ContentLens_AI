import io
import structlog
from typing import Optional
from fastapi import UploadFile
import PyPDF2
import pytesseract
from PIL import Image
import docx

logger = structlog.get_logger(__name__)

class DocumentParserService:
    @staticmethod
    async def parse_file(file: UploadFile) -> Optional[str]:
        logger.info("Parsing file", filename=file.filename, content_type=file.content_type)
        content = await file.read()
        
        try:
            if file.filename.endswith(".pdf"):
                return DocumentParserService._parse_pdf(content)
            elif file.filename.endswith(".docx"):
                return DocumentParserService._parse_docx(content)
            elif file.filename.endswith(".txt"):
                return content.decode("utf-8")
            elif file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
                return DocumentParserService._parse_image(content)
            else:
                logger.warning("Unsupported file type", filename=file.filename)
                return None
        except Exception as e:
            logger.error("Error parsing file", error=str(e), filename=file.filename)
            return None

    @staticmethod
    def _parse_pdf(content: bytes) -> str:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text

    @staticmethod
    def _parse_docx(content: bytes) -> str:
        doc = docx.Document(io.BytesIO(content))
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])

    @staticmethod
    def _parse_image(content: bytes) -> str:
        image = Image.open(io.BytesIO(content))
        # Assuming tesseract is installed in the system PATH
        text = pytesseract.image_to_string(image)
        return text
