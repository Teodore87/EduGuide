# === EduGuide OCR Service ===
# Wraps Google Vision API for text extraction from homework images.
# Falls back to a mock response when API credentials are not configured.

import os
import json


def extract_text_from_image(image_path: str) -> dict:
    """
    Extract text from an image using Google Vision API.

    Args:
        image_path: Path to the uploaded image file.

    Returns:
        dict with keys:
            - 'text': The extracted text string
            - 'language': Detected language code (e.g. 'sv', 'en')
            - 'success': Boolean indicating if extraction worked
            - 'source': 'vision_api' or 'mock'
    """
    # Check if Google Vision credentials are configured
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

    if credentials_path and os.path.exists(credentials_path):
        return _extract_with_vision_api(image_path)
    else:
        raise FileNotFoundError(f"Google Vision credentials not found at {credentials_path}")


def _extract_with_vision_api(image_path: str) -> dict:
    """Use Google Cloud Vision API for real OCR."""
    try:
        from google.cloud import vision

        # Create Vision API client
        client = vision.ImageAnnotatorClient()

        # Read the image file
        with open(image_path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        # Perform text detection
        response = client.text_detection(image=image)

        if response.error.message:
            return {
                "text": "",
                "language": "",
                "success": False,
                "source": "vision_api",
                "error": response.error.message,
            }

        texts = response.text_annotations
        if texts:
            # First annotation contains the full extracted text
            full_text = texts[0].description.strip()
            # Detect language from the first annotation
            language = (
                texts[0].locale if hasattr(texts[0], "locale") else "unknown"
            )
            return {
                "text": full_text,
                "language": language or "unknown",
                "success": True,
                "source": "vision_api",
            }
        else:
            return {
                "text": "",
                "language": "",
                "success": False,
                "source": "vision_api",
                "error": "Ingen text hittades i bilden.",
            }

    except Exception as e:
        return {
            "text": "",
            "language": "",
            "success": False,
            "source": "vision_api",
            "error": str(e),
        }
