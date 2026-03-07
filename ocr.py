from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import re


def extract_text_from_image(image_path: str) -> str:
    """OCR a book cover image and return the most useful search query.

    Preprocesses the image to handle colourful/low-contrast covers (common
    on book covers with yellow-on-orange, white-on-image, etc.) then extracts
    the title from the first meaningful line of text.
    """
    img = Image.open(image_path).convert("RGB")

    # Scale up small images — Tesseract accuracy drops below ~1000px
    w, h = img.size
    if w < 1000:
        scale = 1000 / w
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # Try multiple preprocessings and pick the one with most text
    candidates = []

    for variant in _preprocessed_variants(img):
        raw = pytesseract.image_to_string(variant, config="--psm 3")
        text = _extract_title(raw)
        if text:
            candidates.append((len(text), text))

    if not candidates:
        return ""

    # Return the longest extracted title (most complete)
    return max(candidates)[1]


def _preprocessed_variants(img: Image.Image):
    """Yield several preprocessed versions of the image."""
    # 1. Greyscale + strong contrast boost (catches most coloured covers)
    grey = img.convert("L")
    yield ImageEnhance.Contrast(grey).enhance(3.0)

    # 2. Greyscale + sharpened (helps with blurry text)
    yield grey.filter(ImageFilter.SHARPEN)

    # 3. Original colour image (sometimes works better for clean covers)
    yield img


def _extract_title(raw: str) -> str:
    """Pull the most useful title string out of raw OCR output.

    Strategy: take the first non-trivial line, strip subtitles after
    a colon or em-dash, and collapse whitespace.
    """
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    if not lines:
        return ""

    # Pick the longest of the first 3 lines — usually the main title
    title_line = max(lines[:3], key=len)

    # Strip subtitle (everything after first colon or em-dash)
    title_line = re.split(r"[:\u2014\-]{1,2}", title_line)[0].strip()

    # Remove stray punctuation / noise characters
    title_line = re.sub(r"[^\w\s']", " ", title_line)
    title_line = re.sub(r"\s+", " ", title_line).strip()

    # Reject single words or very short strings — likely noise
    if len(title_line) < 4 or " " not in title_line:
        # Fall back to first two lines joined
        fallback = " ".join(lines[:2])
        fallback = re.sub(r"\s+", " ", fallback).strip()
        return fallback if len(fallback) > 4 else ""

    return title_line
