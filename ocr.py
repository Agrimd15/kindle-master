from PIL import Image
import pytesseract
import re


def extract_text_from_image(image_path: str) -> str:
    """OCR an image and return cleaned text (title + author)."""
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    # Collapse whitespace / newlines
    text = re.sub(r"\s+", " ", text).strip()
    return text
