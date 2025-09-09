import os, time
from typing import Tuple, List, Dict
import redis

# Conectare Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

WINDOW_SEC = 3600  # 1h

# Praguri pentru demo (ajustează în .env dacă vrei)
MAX_NEW_PAYEES_1H = int(os.getenv("MAX_NEW_PAYEES_1H", "3"))
MAX_TOTAL_1H = float(os.getenv("MAX_TOTAL_1H", "50000"))  # RON
FIRST_TO_PAYEE_PENALTY = int(os.getenv("FIRST_TO_PAYEE_PENALTY", "10"))

def _now() -> int:
    return int(time.time())

def _keys(src_iban: str) -> Dict[str, str]:
    base = f"vel:{src_iban}"
    return {
        "payees": f"{base}:payees",       # ZSET: dst_iban cu score=timestamp
        "amounts": f"{base}:amounts",     # ZSET: amount cu score=timestamp
        "meta": f"{base}:meta",           # HASH: counters etc.
    }

def record_and_score(src_iban: str, dst_iban: str, amount: float, is_first_to_payee: bool) -> Tuple[int, List[str]]:
    """
    Înregistrează tranzacția curentă în ferestra de 1h și calculează un extra-score + reasons.
    """
    now = _now()
    k = _keys(src_iban)

    pipe = r.pipeline()
    # Curățăm tot ce e mai vechi de 1h
    min_ts = now - WINDOW_SEC
    pipe.zremrangebyscore(k["payees"], 0, min_ts)
    pipe.zremrangebyscore(k["amounts"], 0, min_ts)

    # Înregistrăm această tranzacție
    pipe.zadd(k["payees"], {dst_iban: now})
    pipe.zadd(k["amounts"], {str(amount): now})
    pipe.execute()

    # Citim starea curentă în fereastră
    uniq_payees = r.zcount(k["payees"], min_ts, now)        # nr. destinații unice
    amounts = [float(a) for a, _ in r.zrangebyscore(k["amounts"], min_ts, now, withscores=True)]
    total_amount = sum(amounts)

    score = 0
    reasons: List[str] = []

    # Mulți beneficiari noi într-o oră => risc
    if uniq_payees > MAX_NEW_PAYEES_1H:
        bump = 10 + 5 * (uniq_payees - MAX_NEW_PAYEES_1H)
        score += bump
        reasons.append(f"Velocity: {uniq_payees} new payees in 1h (+{bump})")

    # Sume totale mari într-o oră => risc
    if total_amount > MAX_TOTAL_1H:
        over = total_amount - MAX_TOTAL_1H
        bump = 10 + min(int(over / 5000), 10)  # max +20
        score += bump
        reasons.append(f"Velocity: {total_amount:.0f} RON in 1h (+{bump})")

    # Prima plată către beneficiar într-un context de spike
    if is_first_to_payee and (uniq_payees > MAX_NEW_PAYEES_1H or total_amount > MAX_TOTAL_1H * 0.7):
        score += FIRST_TO_PAYEE_PENALTY
        reasons.append(f"Velocity: first-to-payee context (+{FIRST_TO_PAYEE_PENALTY})")

    return min(score, 35), reasons  # plafonăm la 35
