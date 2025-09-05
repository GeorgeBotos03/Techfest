import yaml
from typing import Tuple, List

with open("app/rules.yaml", "r") as f:
    RULES = yaml.safe_load(f)

WARN_T = RULES["warn_threshold"]
HOLD_T = RULES["hold_threshold"]

async def score_payment(features: dict, cop_name_match: bool, on_watchlist: bool) -> Tuple[float, str, List[str], int]:
    score = 0.0
    reasons: List[str] = []

    if features.get("amount", 0) >= RULES["high_amount_threshold"]:
        score += 20
        reasons.append("High amount")

    ch = features.get("channel", "web")
    score += RULES["channel_weights"].get(ch, 0)

    if features.get("is_first_to_payee", False):
        score += RULES["first_payment_weight"]
        reasons.append("First payment to beneficiary")

    if on_watchlist:
        score += RULES["watchlist_hit_weight"]
        reasons.append("Beneficiary on watchlist")

    if not cop_name_match:
        score += RULES["name_mismatch_weight"]
        reasons.append("Name/IBAN mismatch (simulated CoP)")

    action = "allow"
    cooloff = 0
    if score >= HOLD_T:
        action = "hold"
        cooloff = RULES["cooloff_minutes"]
    elif score >= WARN_T:
        action = "warn"

    return round(score, 1), action, reasons, cooloff
