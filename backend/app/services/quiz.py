from typing import Tuple, List
from app.schemas import QuizIn

# Reguli simple, explicabile
WEIGHTS = {
    "was_called_by_someone_claiming_bank": 20,
    "was_asked_to_invest_or_crypto": 20,
    "screen_sharing_or_remote_access": 25,
    "not_verified_beneficiary": 15,
}

def score_quiz(q: QuizIn) -> Tuple[int, str, List[str]]:
    score = 0
    reasons: List[str] = []

    if q.was_called_by_someone_claiming_bank:
        score += WEIGHTS["was_called_by_someone_claiming_bank"]
        reasons.append("Caller claimed to be from bank")
    if q.was_asked_to_invest_or_crypto:
        score += WEIGHTS["was_asked_to_invest_or_crypto"]
        reasons.append("Asked to invest/crypto")
    if q.screen_sharing_or_remote_access:
        score += WEIGHTS["screen_sharing_or_remote_access"]
        reasons.append("Screen sharing / remote access")
    if not q.verified_beneficiary_yourself:
        score += WEIGHTS["not_verified_beneficiary"]
        reasons.append("Beneficiary not verified personally")

    # mapping simplu
    action = "release"  # default
    if score >= 40:
        action = "cancel"   # menținem HOLD (sau blocăm)
    elif score >= 20:
        action = "warn"     # menținem WARN

    return score, action, reasons
