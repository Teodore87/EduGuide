# === EduGuide Configuration ===
# Loads environment variables and provides app-wide settings.

import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # --- Flask ---
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")

    # --- Database ---
    # SQLite database stored in the project directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'eduguide.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Google Vision API (OCR) ---
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

    # --- Google Gemini API (AI Reasoning) ---
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    # --- Parent Dashboard ---
    PARENT_PIN = os.getenv("PARENT_PIN", "1234")

    # --- Upload Settings ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
