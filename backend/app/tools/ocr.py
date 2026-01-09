import pytesseract
from PIL import Image
from ..core.logging import logger

def perform_ocr(file_path: str) -> str:
    """
    Stand-alone OCR tool to extract text from images.
    """
    try:
        logger.info(f"Tool: Starting OCR for {file_path}")
        img = Image.open(file_path)
        # We can add custom config here for better Arabic/English detection
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        logger.error(f"OCR Tool Error: {e}")
        return ""