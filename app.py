# === EduGuide - Main Flask Application ===
# Entry point for the pedagogical homework helper app.
# Handles page routes and API endpoints for the student and parent interfaces.

import os
import json
import uuid
from datetime import datetime, timezone

from flask import (
    Flask, render_template, request, jsonify, session, redirect, url_for
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from models import db, Student, Session as StudySession, Question, ParentAccess
from services.ocr_service import extract_text_from_image
from services.ai_service import (
    detect_subject, reformulate_question, generate_hint, validate_answer
)
from services.xp_service import calculate_xp, get_level


# ============================================================
# APP FACTORY
# ============================================================

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)

    # Ensure upload folder exists
    os.makedirs(app.config.get("UPLOAD_FOLDER", "uploads"), exist_ok=True)

    # Create database tables on first run
    with app.app_context():
        db.create_all()

    # Register routes
    register_routes(app)

    return app


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    allowed = Config.ALLOWED_EXTENSIONS
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def get_current_student():
    """Get the current student from the session, or None."""
    student_id = session.get("student_id")
    if student_id:
        return Student.query.get(student_id)
    return None


# ============================================================
# ROUTE REGISTRATION
# ============================================================

def register_routes(app):
    """Register all page routes and API endpoints."""

    # ----------------------------------------------------------
    # PAGE ROUTES
    # ----------------------------------------------------------

    @app.route("/")
    def index():
        """Landing page — persona selection."""
        student = get_current_student()
        return render_template("index.html", student=student)

    @app.route("/study")
    def study():
        """Main homework helper interface."""
        student = get_current_student()
        if not student:
            return redirect(url_for("index"))
        level_info = get_level(student.total_xp)
        return render_template("study.html", student=student, level=level_info)

    @app.route("/parent")
    def parent():
        """Parent dashboard — PIN protected."""
        return render_template("parent.html")

    # ----------------------------------------------------------
    # API: STUDENT MANAGEMENT
    # ----------------------------------------------------------

    @app.route("/api/create-student", methods=["POST"])
    def api_create_student():
        """Create a new student profile and start a session."""
        data = request.get_json()
        name = data.get("name", "").strip()
        persona = data.get("persona", "explorer")

        if not name:
            return jsonify({"error": "Namn krävs"}), 400

        if persona not in ("explorer", "gamer", "coach", "zen"):
            return jsonify({"error": "Ogiltig persona"}), 400

        # Create student
        student = Student(name=name, persona=persona)
        db.session.add(student)
        db.session.commit()

        # Create default parent access with configured PIN
        pin = Config.PARENT_PIN
        parent_access = ParentAccess(
            student_id=student.id,
            pin_hash=generate_password_hash(pin),
        )
        db.session.add(parent_access)
        db.session.commit()

        # Store in session
        session["student_id"] = student.id

        return jsonify({
            "success": True,
            "student_id": student.id,
            "name": student.name,
            "persona": student.persona,
        })

    @app.route("/api/select-student", methods=["POST"])
    def api_select_student():
        """Select an existing student profile."""
        data = request.get_json()
        student_id = data.get("student_id")

        student = Student.query.get(student_id)
        if not student:
            return jsonify({"error": "Eleven hittades inte"}), 404

        session["student_id"] = student.id

        return jsonify({
            "success": True,
            "student_id": student.id,
            "name": student.name,
            "persona": student.persona,
            "total_xp": student.total_xp,
        })

    # ----------------------------------------------------------
    # API: IMAGE UPLOAD & OCR
    # ----------------------------------------------------------

    @app.route("/api/upload-image", methods=["POST"])
    def api_upload_image():
        """Upload a homework image and extract text via OCR."""
        student = get_current_student()
        if not student:
            return jsonify({"error": "Ingen elev vald"}), 401

        if "image" not in request.files:
            return jsonify({"error": "Ingen bild bifogades"}), 400

        file = request.files["image"]
        if file.filename == "":
            return jsonify({"error": "Ingen fil vald"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Otillåten filtyp. Använd PNG, JPG eller WEBP."}), 400

        # Save uploaded file
        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # Extract text using OCR service
        result = extract_text_from_image(filepath)

        if result["success"]:
            # Start a new study session
            study_session = StudySession(
                student_id=student.id,
                subject=detect_subject(result["text"]),
            )
            db.session.add(study_session)
            db.session.commit()

            session["current_session_id"] = study_session.id

            # Create the question record
            question = Question(
                session_id=study_session.id,
                original_text=result["text"],
                image_path=filepath,
                subject=study_session.subject,
            )
            db.session.add(question)
            db.session.commit()

            session["current_question_id"] = question.id

            return jsonify({
                "success": True,
                "text": result["text"],
                "subject": study_session.subject,
                "question_id": question.id,
                "source": result["source"],
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get("error", "Kunde inte läsa texten i bilden."),
            }), 500

    # ----------------------------------------------------------
    # API: TEXT INPUT (manual, no image)
    # ----------------------------------------------------------

    @app.route("/api/submit-text", methods=["POST"])
    def api_submit_text():
        """Submit homework question as text (without image)."""
        student = get_current_student()
        if not student:
            return jsonify({"error": "Ingen elev vald"}), 401

        data = request.get_json()
        text = data.get("text", "").strip()

        if not text:
            return jsonify({"error": "Ingen text angavs"}), 400

        subject = detect_subject(text)

        # Start a new study session
        study_session = StudySession(
            student_id=student.id,
            subject=subject,
        )
        db.session.add(study_session)
        db.session.commit()

        session["current_session_id"] = study_session.id

        # Create question record
        question = Question(
            session_id=study_session.id,
            original_text=text,
            subject=subject,
        )
        db.session.add(question)
        db.session.commit()

        session["current_question_id"] = question.id

        return jsonify({
            "success": True,
            "text": text,
            "subject": subject,
            "question_id": question.id,
        })

    # ----------------------------------------------------------
    # API: SCAFFOLDING (reformulate, hint, validate)
    # ----------------------------------------------------------

    @app.route("/api/reformulate", methods=["POST"])
    def api_reformulate():
        """Get 3 reformulated versions of the current question."""
        student = get_current_student()
        if not student:
            return jsonify({"error": "Ingen elev vald"}), 401

        question_id = session.get("current_question_id")
        question = Question.query.get(question_id)

        if not question:
            return jsonify({"error": "Ingen aktiv fråga"}), 404

        result = reformulate_question(question.original_text, student.persona)

        if result["success"]:
            # Store reformulations in the database
            question.reformulations = json.dumps({
                "simple": result["simple"],
                "context": result["context"],
                "steps": result["steps"],
            })
            db.session.commit()

        return jsonify(result)

    @app.route("/api/hint", methods=["POST"])
    def api_hint():
        """Get a progressive hint for the current question."""
        student = get_current_student()
        if not student:
            return jsonify({"error": "Ingen elev vald"}), 401

        question_id = session.get("current_question_id")
        question = Question.query.get(question_id)

        if not question:
            return jsonify({"error": "Ingen aktiv fråga"}), 404

        # Increment hint count
        question.hint_count += 1
        db.session.commit()

        result = generate_hint(
            question.original_text, student.persona, question.hint_count
        )

        return jsonify({
            **result,
            "hint_number": question.hint_count,
        })

    @app.route("/api/submit-answer", methods=["POST"])
    def api_submit_answer():
        """Submit an answer for validation."""
        student = get_current_student()
        if not student:
            return jsonify({"error": "Ingen elev vald"}), 401

        data = request.get_json()
        answer = data.get("answer", "").strip()

        if not answer:
            return jsonify({"error": "Inget svar angavs"}), 400

        question_id = session.get("current_question_id")
        question = Question.query.get(question_id)

        if not question:
            return jsonify({"error": "Ingen aktiv fråga"}), 404

        # Increment attempts
        question.attempts += 1

        # Validate answer using AI
        validation = validate_answer(
            question.original_text, answer, student.persona
        )

        # Calculate XP
        xp_result = calculate_xp(
            hint_count=question.hint_count,
            attempts=question.attempts,
            is_correct=validation.get("is_correct", False),
        )

        if validation.get("is_correct"):
            question.is_correct = True
            question.xp_earned = xp_result["xp"]
            student.total_xp += xp_result["xp"]

            # End the session
            study_session = StudySession.query.get(question.session_id)
            if study_session:
                study_session.ended_at = datetime.now(timezone.utc)

        db.session.commit()

        level_info = get_level(student.total_xp)

        return jsonify({
            "is_correct": validation.get("is_correct", False),
            "feedback": validation.get("feedback", ""),
            "xp_earned": xp_result["xp"],
            "xp_message": xp_result["message"],
            "badge": xp_result["badge"],
            "suggest_break": xp_result["suggest_break"],
            "total_xp": student.total_xp,
            "level": level_info,
            "attempts": question.attempts,
        })

    # ----------------------------------------------------------
    # API: XP & PROGRESS
    # ----------------------------------------------------------

    @app.route("/api/xp")
    def api_xp():
        """Get current student's XP and level info."""
        student = get_current_student()
        if not student:
            return jsonify({"error": "Ingen elev vald"}), 401

        level_info = get_level(student.total_xp)
        return jsonify(level_info)

    @app.route("/api/students")
    def api_students():
        """List all students (for student selection)."""
        students = Student.query.all()
        return jsonify([
            {
                "id": s.id,
                "name": s.name,
                "persona": s.persona,
                "total_xp": s.total_xp,
            }
            for s in students
        ])

    # ----------------------------------------------------------
    # API: PARENT DASHBOARD
    # ----------------------------------------------------------

    @app.route("/api/parent/login", methods=["POST"])
    def api_parent_login():
        """Authenticate parent with PIN."""
        data = request.get_json()
        pin = data.get("pin", "")

        # Check against configured PIN
        if pin == Config.PARENT_PIN:
            session["parent_authenticated"] = True
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Fel PIN-kod"}), 401

    @app.route("/api/parent/progress")
    def api_parent_progress():
        """Get all students' progress data for the parent dashboard."""
        if not session.get("parent_authenticated"):
            return jsonify({"error": "Ej inloggad"}), 401

        students = Student.query.all()
        progress = []

        for student in students:
            # Get all sessions for this student
            sessions = StudySession.query.filter_by(student_id=student.id).all()

            # Calculate stats
            total_questions = 0
            correct_answers = 0
            total_time_minutes = 0
            subject_counts = {}
            struggle_areas = []

            for s in sessions:
                questions = Question.query.filter_by(session_id=s.id).all()
                for q in questions:
                    total_questions += 1
                    if q.is_correct:
                        correct_answers += 1
                    # Track subjects
                    subj = q.subject or "övrigt"
                    subject_counts[subj] = subject_counts.get(subj, 0) + 1
                    # Track struggle areas (needed 3+ hints or attempts)
                    if q.hint_count >= 2 or q.attempts >= 3:
                        struggle_areas.append({
                            "subject": subj,
                            "question": q.original_text[:80],
                            "hints_used": q.hint_count,
                            "attempts": q.attempts,
                        })

                # Calculate time spent
                if s.started_at and s.ended_at:
                    delta = s.ended_at - s.started_at
                    total_time_minutes += delta.total_seconds() / 60

            level_info = get_level(student.total_xp)

            progress.append({
                "student_id": student.id,
                "name": student.name,
                "persona": student.persona,
                "total_xp": student.total_xp,
                "level": level_info,
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "accuracy": round(
                    (correct_answers / total_questions * 100) if total_questions > 0 else 0
                ),
                "total_time_minutes": round(total_time_minutes, 1),
                "subjects": subject_counts,
                "struggle_areas": struggle_areas[:5],  # Top 5 struggle areas
            })

        return jsonify(progress)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
