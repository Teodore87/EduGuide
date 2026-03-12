# === EduGuide XP Service ===
# Handles experience point calculations, rewards, and growth-mindset feedback.

import random


# --- XP Constants ---
XP_FIRST_TRY = 10      # Correct on first attempt, no hints
XP_WITH_HINTS = 5       # Correct after using hints
XP_NO_PENALTY = 0       # Never negative — growth mindset!

# --- Encouraging Messages (Swedish) ---
FIRST_TRY_MESSAGES = [
    "Helt rätt på första försöket! Du är en stjärna! ⭐",
    "Wow, perfekt! Du behövde inga ledtrådar alls! 🎯",
    "Fantastiskt! Du löste det direkt! 🚀",
    "Strålande jobbat! Fullpoäng! 🌟",
    "Imponerande! Du knäckte det på en gång! 💪",
]

PERSISTENCE_MESSAGES = [
    "Du gav inte upp och det lönade sig! Bra kämpat! 💪",
    "Uthållighet lönar sig! Snyggt jobbat! 🎉",
    "Du fortsatte försöka och lyckades! Det är riktigt starkt! 🌈",
    "Varje försök gör dig smartare. Och nu fick du rätt! 🧠",
    "Du klättrade uppåt och nådde toppen! Fantastiskt! 🏔️",
]

ENCOURAGEMENT_MESSAGES = [
    "Du kommer närmare! Fortsätt så! 💫",
    "Bra försök! Varje gång lär du dig något nytt. 🌱",
    "Inte riktigt, men du är på rätt spår! 🛤️",
    "Ge inte upp! Du lär dig med varje försök. 📚",
    "Nästan! Försök tänka på det från en annan vinkel. 🔄",
]

BREAK_SUGGESTION_MESSAGES = [
    "Du har jobbat hårt! Vill du ta en liten paus? ☕",
    "Ibland hjälper det att ta ett steg tillbaka. Vill du prova en annan fråga? 🌿",
    "Låt oss ta en paus eller prova ett annat sätt! Du har gjort ett bra jobb. 🌸",
]


def calculate_xp(hint_count: int, attempts: int, is_correct: bool) -> dict:
    """
    Calculate XP earned for a question attempt.

    Args:
        hint_count: Number of hints the student used.
        attempts: Number of answer attempts made.
        is_correct: Whether the answer was eventually correct.

    Returns:
        dict with:
            - 'xp': Points earned (never negative)
            - 'message': Encouraging feedback in Swedish
            - 'badge': Optional badge type ('first_try', 'persistent', None)
            - 'suggest_break': Whether to suggest a break (after 3+ wrong attempts)
    """
    result = {
        "xp": XP_NO_PENALTY,
        "message": "",
        "badge": None,
        "suggest_break": False,
    }

    if is_correct:
        if hint_count == 0 and attempts <= 1:
            # Perfect — correct on first try with no hints
            result["xp"] = XP_FIRST_TRY
            result["message"] = random.choice(FIRST_TRY_MESSAGES)
            result["badge"] = "first_try"
        else:
            # Got it right after some effort
            result["xp"] = XP_WITH_HINTS
            result["message"] = random.choice(PERSISTENCE_MESSAGES)
            result["badge"] = "persistent"
    else:
        # Not correct yet — encourage without penalizing
        result["message"] = random.choice(ENCOURAGEMENT_MESSAGES)

        # After 3+ incorrect attempts, suggest a break
        if attempts >= 3:
            result["suggest_break"] = True
            result["message"] = random.choice(BREAK_SUGGESTION_MESSAGES)

    return result


def get_level(total_xp: int) -> dict:
    """
    Calculate the student's current level based on total XP.

    Returns:
        dict with:
            - 'level': Current level number
            - 'title': Level title in Swedish
            - 'xp_for_next': XP needed for the next level
            - 'progress': Progress percentage toward next level (0-100)
    """
    # Level thresholds — each level requires progressively more XP
    levels = [
        (0, "Nybörjare 🌱"),          # Beginner
        (50, "Upptäckare 🔍"),        # Discoverer
        (150, "Lärling 📚"),          # Apprentice
        (300, "Kunskapsjägare 🎯"),   # Knowledge Hunter
        (500, "Mästare 🏆"),          # Master
        (800, "Legendar ⭐"),         # Legend
        (1200, "Geni 🧠"),           # Genius
    ]

    current_level = 0
    current_title = levels[0][1]
    xp_for_next = levels[1][0] if len(levels) > 1 else levels[0][0]
    current_threshold = 0

    for i, (threshold, title) in enumerate(levels):
        if total_xp >= threshold:
            current_level = i + 1
            current_title = title
            current_threshold = threshold
            if i + 1 < len(levels):
                xp_for_next = levels[i + 1][0]
            else:
                xp_for_next = threshold  # Max level reached

    # Calculate progress toward next level
    if current_level < len(levels):
        xp_in_level = total_xp - current_threshold
        xp_needed = xp_for_next - current_threshold
        progress = min(100, int((xp_in_level / xp_needed) * 100)) if xp_needed > 0 else 100
    else:
        progress = 100

    return {
        "level": current_level,
        "title": current_title,
        "xp_for_next": xp_for_next,
        "progress": progress,
        "total_xp": total_xp,
    }
