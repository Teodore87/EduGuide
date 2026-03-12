# === EduGuide AI Service ===
# Wraps Google Gemini API for scaffolding, question reformulation,
# hint generation, and answer validation.
# Falls back to mock responses when API key is not configured.

import os
import json


# --- Persona prompt templates (internal instructions in English) ---
PERSONA_PROMPTS = {
    "explorer": (
        "You are 'The Explorer', a guide who explains concepts using analogies "
        "from space, nature, and exploration. Use phrases like 'Let's discover...', "
        "'Think of it like a journey through...'. Be curious and wonder-filled."
    ),
    "gamer": (
        "You are 'The Gamer', who explains concepts through game mechanics. "
        "Use phrases like 'Level up your knowledge...', 'This is like a puzzle...', "
        "'You've unlocked a new skill!'. Be energetic and fun."
    ),
    "coach": (
        "You are 'The Coach', high energy and encouraging. Break things into "
        "'drills' and 'practice rounds'. Use phrases like 'Great hustle!', "
        "'Let's break this down into plays...', 'You're crushing it!'"
    ),
    "zen": (
        "You are 'The Zen Master', calm and reassuring. Use simple language "
        "and short sentences. Focus on removing stress. Use phrases like "
        "'Take a breath...', 'One step at a time...', 'There's no rush.'"
    ),
}

# Base system instruction for all scaffolding interactions
SYSTEM_INSTRUCTION = """You are EduGuide, a pedagogical AI assistant for students aged 10-15.
Your mission is to help students UNDERSTAND their homework through scaffolding.

CRITICAL RULES:
1. NEVER reveal the final answer directly.
2. Guide the student step by step toward understanding.
3. Use encouraging, growth-mindset language.
4. All student-facing text MUST be in Swedish.
5. Adapt your tone to the selected persona.
6. If the student seems frustrated, stay calm and suggest a break or different approach.
"""


def detect_subject(text: str) -> str:
    """
    Detect the subject area of a homework question.

    Args:
        text: The homework question text.

    Returns:
        Subject string in Swedish: 'matematik', 'naturvetenskap', 'svenska', 'engelska',
        'historia', 'geografi', or 'övrigt'.
    """
    api_key = os.getenv("GEMINI_API_KEY", "")

    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    
    return _detect_subject_gemini(text, api_key)


def reformulate_question(text: str, persona: str = "explorer") -> dict:
    """
    Generate 3 reformulated versions of a homework question.

    Args:
        text: The original homework question.
        persona: The student's selected persona.

    Returns:
        dict with keys:
            - 'simple': A simpler version of the question
            - 'context': The question with real-world context
            - 'steps': The question broken into step-by-step parts
            - 'subject': Detected subject area
            - 'success': Boolean
            - 'source': 'gemini' or 'mock'
    """
    api_key = os.getenv("GEMINI_API_KEY", "")

    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
        
    return _reformulate_gemini(text, persona, api_key)


def generate_hint(text: str, persona: str, hint_number: int) -> dict:
    """
    Generate a progressive hint for a homework question.

    Args:
        text: The original homework question.
        persona: The student's selected persona.
        hint_number: Which hint this is (1, 2, 3...). Later hints are more specific.

    Returns:
        dict with 'hint' (string), 'success' (bool), 'source' (string)
    """
    api_key = os.getenv("GEMINI_API_KEY", "")

    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
        
    return _generate_hint_gemini(text, persona, hint_number, api_key)


def validate_answer(question_text: str, student_answer: str, persona: str) -> dict:
    """
    Check if a student's answer is correct WITHOUT revealing the right answer.

    Args:
        question_text: The original homework question.
        student_answer: The student's submitted answer.
        persona: The student's persona for feedback tone.

    Returns:
        dict with:
            - 'is_correct': Boolean
            - 'feedback': Encouraging feedback in Swedish
            - 'success': Boolean
            - 'source': 'gemini' or 'mock'
    """
    api_key = os.getenv("GEMINI_API_KEY", "")

    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
        
    return _validate_gemini(question_text, student_answer, persona, api_key)


# ============================================================
# GEMINI API IMPLEMENTATIONS
# ============================================================

def _detect_subject_gemini(text: str, api_key: str) -> str:
    """Use Gemini to classify the question subject."""
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-flash-latest")

        prompt = (
            "Classify the following homework question into exactly ONE of these "
            "Swedish subject categories: matematik, naturvetenskap, svenska, engelska, "
            "historia, geografi, övrigt.\n\n"
            "Respond with ONLY the category name, nothing else.\n\n"
            f"Question: {text}"
        )

        response = model.generate_content(prompt)
        subject = response.text.strip().lower()

        valid_subjects = [
            "matematik", "naturvetenskap", "svenska",
            "engelska", "historia", "geografi", "övrigt",
        ]
        return subject if subject in valid_subjects else "övrigt"

    except Exception as e:
        raise e


def _reformulate_gemini(text: str, persona: str, api_key: str) -> dict:
    """Use Gemini to generate 3 reformulations."""
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            "gemini-flash-latest",
            system_instruction=SYSTEM_INSTRUCTION + "\n\n" + PERSONA_PROMPTS.get(persona, ""),
        )

        prompt = (
            "A student needs help understanding this homework question. "
            "Generate 3 different reformulations in Swedish:\n\n"
            f"Original question: {text}\n\n"
            "Return a JSON object with exactly these keys:\n"
            '- "simple": A simpler, clearer version of the question\n'
            '- "context": The question explained with a real-world example or analogy\n'
            '- "steps": The question broken into numbered steps to solve it\n\n'
            "REMEMBER: Do NOT reveal the answer. Only rephrase the question.\n"
            "Respond with ONLY the JSON object, no markdown formatting."
        )

        response = model.generate_content(prompt)
        result = json.loads(response.text.strip())

        subject = _detect_subject_gemini(text, api_key)

        return {
            "simple": result.get("simple", ""),
            "context": result.get("context", ""),
            "steps": result.get("steps", ""),
            "subject": subject,
            "success": True,
            "source": "gemini",
        }

    except Exception as e:
        raise e


def _generate_hint_gemini(text: str, persona: str, hint_number: int, api_key: str) -> dict:
    """Use Gemini to generate a progressive hint."""
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            "gemini-flash-latest",
            system_instruction=SYSTEM_INSTRUCTION + "\n\n" + PERSONA_PROMPTS.get(persona, ""),
        )

        specificity = {
            1: "Give a very general hint — just point the student in the right direction.",
            2: "Give a more specific hint — suggest a method or approach to use.",
            3: "Give a detailed hint — walk through the first step of the solution, but do NOT give the final answer.",
        }
        level = specificity.get(min(hint_number, 3), specificity[3])

        prompt = (
            f"A student is stuck on this homework question:\n\n{text}\n\n"
            f"This is hint #{hint_number}. {level}\n\n"
            "Write the hint in Swedish. Be encouraging and use growth-mindset language.\n"
            "NEVER reveal the final answer."
        )

        response = model.generate_content(prompt)

        return {
            "hint": response.text.strip(),
            "success": True,
            "source": "gemini",
        }

    except Exception as e:
        raise e


def _validate_gemini(question: str, answer: str, persona: str, api_key: str) -> dict:
    """Use Gemini to check the answer without revealing the solution."""
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            "gemini-flash-latest",
            system_instruction=SYSTEM_INSTRUCTION + "\n\n" + PERSONA_PROMPTS.get(persona, ""),
        )

        prompt = (
            "A student answered a homework question. Evaluate if they are correct.\n\n"
            f"Question: {question}\n"
            f"Student's answer: {answer}\n\n"
            "Return a JSON object with:\n"
            '- "is_correct": true or false\n'
            '- "feedback": Encouraging feedback in Swedish. If wrong, give a gentle nudge '
            "toward the right direction WITHOUT revealing the answer.\n\n"
            "Respond with ONLY the JSON object, no markdown formatting."
        )

        response = model.generate_content(prompt)
        result = json.loads(response.text.strip())

        return {
            "is_correct": result.get("is_correct", False),
            "feedback": result.get("feedback", "Bra försök!"),
            "success": True,
            "source": "gemini",
        }

    except Exception as e:
        raise e


