# === EduGuide Database Models ===
# Defines the SQLAlchemy models for students, sessions, questions, and parent access.

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance (attached to app in app.py)
db = SQLAlchemy()


class Student(db.Model):
    """
    Represents a student user.
    Each student selects a persona and accumulates XP over time.
    """
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # Persona: 'explorer', 'gamer', 'coach', or 'zen'
    persona = db.Column(db.String(20), nullable=False, default="explorer")
    total_xp = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    sessions = db.relationship("Session", backref="student", lazy=True)
    parent_access = db.relationship("ParentAccess", backref="student", lazy=True)

    def __repr__(self):
        return f"<Student {self.name} ({self.persona}) XP:{self.total_xp}>"


class Session(db.Model):
    """
    A study session — one sitting where a student works on homework.
    Tracks subject area, start/end time, and all questions attempted.
    """
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id"), nullable=False
    )
    # Detected subject: 'matematik', 'naturvetenskap', 'språk', 'övrigt', etc.
    subject = db.Column(db.String(50), nullable=True)
    started_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    ended_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    questions = db.relationship("Question", backref="session", lazy=True)

    def __repr__(self):
        return f"<Session {self.id} student={self.student_id} subject={self.subject}>"


class Question(db.Model):
    """
    A single homework question within a session.
    Stores the original text (from OCR or typed), reformulations,
    hint usage, attempts, and XP earned.
    """
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer, db.ForeignKey("sessions.id"), nullable=False
    )
    # Original text extracted from image (OCR) or typed by student
    original_text = db.Column(db.Text, nullable=False)
    # Path to uploaded image (if any)
    image_path = db.Column(db.String(255), nullable=True)
    # JSON string containing the 3 reformulated versions of the question
    reformulations = db.Column(db.Text, nullable=True)
    # Detected subject for this specific question
    subject = db.Column(db.String(50), nullable=True)
    # How many hints the student requested
    hint_count = db.Column(db.Integer, nullable=False, default=0)
    # Number of answer attempts
    attempts = db.Column(db.Integer, nullable=False, default=0)
    # Whether the student eventually got it right
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    # XP earned for this question (+10 first try, +5 with hints, 0 if not solved)
    xp_earned = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<Question {self.id} correct={self.is_correct} xp={self.xp_earned}>"


class ParentAccess(db.Model):
    """
    Links a parent PIN to a student for dashboard access.
    Uses a hashed PIN for basic security.
    """
    __tablename__ = "parent_access"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id"), nullable=False
    )
    # Hashed PIN for parent dashboard access
    pin_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<ParentAccess student={self.student_id}>"
