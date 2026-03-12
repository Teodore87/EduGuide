# === EduGuide OCR Service ===
# Wraps Google Vision API for text extraction from homework images.
# Falls back to a mock response when API credentials are not configured.

import os
import json


def extract_text_from_image(image_path: str) -> dict:
    """
    Extract text from an image using Google Vision API.
    """
    # Check if Google Vision credentials are configured as a file path
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    # Or as a JSON string (common for cloud deployments like Render)
    credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON", "")

    if (credentials_path and os.path.exists(credentials_path)) or credentials_json:
        return _extract_with_vision_api(image_path, credentials_json)
    else:
        # If no credentials, we can't do real OCR
        return {
            "text": "DEBUG: OCR skulle skett här, men inga referenser hittades.",
            "language": "sv",
            "success": False,
            "source": "mock",
            "error": "Google Vision credentials not configured."
        }


def _extract_with_vision_api(image_path: str, credentials_json: str = "") -> dict:
    """Use Google Cloud Vision API for real OCR."""
    try:
        from google.cloud import vision
        from google.oauth2 import service_account

        # Create Vision API client
        if credentials_json:
            # Load from JSON string
            info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(info)
            client = vision.ImageAnnotatorClient(credentials=credentials)
        else:
            # Load from file (default behavior using GOOGLE_APPLICATION_CREDENTIALS env var)
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
