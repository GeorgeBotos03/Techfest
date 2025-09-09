# -*- coding: utf-8 -*-
from typing import Tuple, List

# Cuvinte-cheie des întâlnite în scam (investment / romance / urgent / refund etc.)
KEYWORDS = {
    "invest": 10, "investment": 10, "crypto": 12, "bitcoin": 12, "nft": 10,
    "urgent": 8, "tax": 6, "refund": 6, "donation": 6, "loan": 6,
    "broker": 8, "exchange": 8, "profit": 8, "fast": 5, "quick": 5,
    "gift": 4, "giveaway": 6, "love": 4, "romance": 6,
}

# Expresii multicuvânt (bonus scor)
KEYPHRASES = {
    "investment opportunity": 12,
    "crypto exchange": 12,
    "fast profit": 10,
    "tax refund": 10,
    "urgent transfer": 9,
}

def text_risk(description: str | None) -> Tuple[int, List[str]]:
    """
    Întoarce (extra_score, reasons) pe baza textului.
    Limităm contribuția totală la max 30 puncte.
    """
    if not description:
        return 0, []
    desc = description.lower()
    score = 0
    reasons: List[str] = []

    for ph, w in KEYPHRASES.items():
        if ph in desc:
            score += w
            reasons.append(f"Keyword: '{ph}'")

    for kw, w in KEYWORDS.items():
        if kw in desc:
            score += w
            reasons.append(f"Keyword: '{kw}'")

    return min(score, 30), reasons
