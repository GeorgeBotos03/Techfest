import os
import redis
from typing import List

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
SET = "watchlist:ibans"

def add_iban(iban: str) -> None:
    r.sadd(SET, iban.upper())

def remove_iban(iban: str) -> None:
    r.srem(SET, iban.upper())

def list_ibans() -> List[str]:
    return sorted(r.smembers(SET))

def is_watchlisted(iban: str) -> bool:
    return r.sismember(SET, iban.upper())
