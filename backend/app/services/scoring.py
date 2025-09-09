from typing import Tuple, List, Dict

# Importăm semnalele specifice scam
from app.services.text_signals import text_risk
from app.services.velocity import record_and_score

# Praguri & ponderi (reguli explicabile)
AMOUNT_WARN = 5000
AMOUNT_HOLD = 10000

BASE_WEIGHTS = {
    "amount_high": 25,           # >5000
    "amount_very_high": 35,      # >10000
    "first_to_payee": 15,
    "cop_mismatch": 20,          # nume/IBAN nu corespund
    "watchlist": 30,             # destinatar pe watchlist
}

def score_payment(features: Dict, cop_ok: bool, on_watchlist: bool) -> Tuple[float, str, List[str], int]:
    """
    Returnează (risk_score, action, reasons, cooloff_minutes)
    Logică orientată pe SCAM:
      - reguli explicabile + text_risk + velocity (Redis)
      - thresholds: <30 allow, 30-59 warn, >=60 hold
    """
    score = 0
    reasons: List[str] = []

    amount = float(features.get("amount", 0))
    is_first = bool(features.get("is_first_to_payee"))

    # 1) Amount rules (explicabile)
    if amount > AMOUNT_HOLD:
        score += BASE_WEIGHTS["amount_very_high"]
        reasons.append("Very high amount")
    elif amount > AMOUNT_WARN:
        score += BASE_WEIGHTS["amount_high"]
        reasons.append("High amount")

    # 2) First to payee
    if is_first:
        score += BASE_WEIGHTS["first_to_payee"]
        reasons.append("First payment to beneficiary")

    # 3) Confirmation of Payee
    if not cop_ok:
        score += BASE_WEIGHTS["cop_mismatch"]
        reasons.append("Name/IBAN mismatch (simulated CoP)")

    # 4) Watchlist
    if on_watchlist:
        score += BASE_WEIGHTS["watchlist"]
        reasons.append("Beneficiary on watchlist")

    # 5) Text signals (descriere – investment/crypto/urgent/romance…)
    desc = features.get("description")
    ts_score, ts_reasons = text_risk(desc)
    if ts_score:
        score += ts_score
        reasons.extend(ts_reasons)

    # 6) Velocity (ferestră 1h, Redis) – spike de beneficiari/sume
    src = features.get("src_iban")
    dst = features.get("dst_iban")
    if src and dst:
        vel_score, vel_reasons = record_and_score(src, dst, amount, is_first)
        if vel_score:
            score += vel_score
            reasons.extend(vel_reasons)

    # Mapping la acțiuni
    action = "allow"
    cooloff = 0
    if score >= 60:
        action = "hold"
        cooloff = 30
    elif score >= 30:
        action = "warn"
        cooloff = 15

    return float(score), action, reasons, cooloff
