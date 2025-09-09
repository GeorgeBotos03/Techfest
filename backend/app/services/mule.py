# -*- coding: utf-8 -*-
from __future__ import annotations
import time
from typing import Dict, List, Tuple, Optional

# Redis client îl primim din deps (get_redis)
# În velocity probabil îl folosești deja; dacă nu, poți face un Redis(host=..., port=...) aici.

PREFIX = "mule"  # cheie de prefix în Redis

def _now() -> float:
    return time.time()

def _to_epoch(ts_iso: str) -> float:
    """
    Acceptă timestamp ISO8601 (ex: '2025-09-06T12:00:00Z') sau '' și întoarce epoch sec.
    Dacă nu primește nimic, folosește time.time().
    """
    if not ts_iso:
        return _now()
    try:
        # format simplu: 'YYYY-MM-DDTHH:MM:SSZ'
        from datetime import datetime, timezone
        dt = datetime.strptime(ts_iso.replace("Z",""), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return _now()

def _k_in_sources(iban: str) -> str:
    return f"{PREFIX}:in_sources:{iban}"   # ZSET (member = src_iban, score = last_ts)

def _k_in_events(iban: str) -> str:
    return f"{PREFIX}:in_events:{iban}"    # ZSET (member = unique_id/ts, score = ts)

def _k_out_dests(iban: str) -> str:
    return f"{PREFIX}:out_dests:{iban}"    # ZSET (member = dst_iban, score = last_ts)

def _k_out_events(iban: str) -> str:
    return f"{PREFIX}:out_events:{iban}"   # ZSET (member = unique_id/ts, score = ts)

def record_payment(rds, *, ts_iso: str, src_iban: str, dst_iban: str) -> None:
    """
    Înregistrează tranzacția în "radarul" de mule.
    Folosește ZSET-uri pt. a păstra doar ultimele `window_sec` la citire (pruning la read).
    """
    ts = _to_epoch(ts_iso)
    # fan-in pentru destinație
    rds.zadd(_k_in_sources(dst_iban), {src_iban: ts})           # last seen per sursă
    rds.zadd(_k_in_events(dst_iban), {f"{ts}:{src_iban}": ts})  # evenimente brute

    # fan-out pentru sursă
    rds.zadd(_k_out_dests(src_iban), {dst_iban: ts})
    rds.zadd(_k_out_events(src_iban), {f"{ts}:{dst_iban}": ts})

def _window_prune(rds, key: str, since_ts: float) -> None:
    # șterge tot ce e mai vechi decât since_ts
    rds.zremrangebyscore(key, 0, since_ts - 0.0001)

def _stats_for_iban(rds, iban: str, hours: int = 24) -> Dict:
    """
    Returnează statistici 'ultimele N ore' pentru un IBAN (ca destinație și ca sursă).
    """
    now = _now()
    window_sec = hours * 3600
    since = now - window_sec

    # prune pe chei relevante
    for key in (_k_in_sources(iban), _k_in_events(iban), _k_out_dests(iban), _k_out_events(iban)):
        _window_prune(rds, key, since)

    # fan-in (câte surse unice au trimis către acest iban)
    fan_in_unique = rds.zcard(_k_in_sources(iban))
    tx_in_count   = rds.zcount(_k_in_events(iban), since, now)

    # fan-out (dacă acest iban a fost sursă către alți destinatari)
    fan_out_unique = rds.zcard(_k_out_dests(iban))
    tx_out_count   = rds.zcount(_k_out_events(iban), since, now)

    # exemple (max 5) – cele mai recente surse/destinații
    recent_sources = [m.decode() if isinstance(m, bytes) else m
                      for m in rds.zrevrange(_k_in_sources(iban), 0, 4)]
    recent_dests = [m.decode() if isinstance(m, bytes) else m
                    for m in rds.zrevrange(_k_out_dests(iban), 0, 4)]

    # scor simplu (tunable): fan-in unic + volum + fan-out
    score = 0
    score += min(60, fan_in_unique * 10)      # 0..60
    score += min(30, tx_in_count * 2)         # 0..30
    score += min(10, fan_out_unique * 2)      # 0..10
    score = int(min(100, score))

    return {
        "iban": iban,
        "hours": hours,
        "mule_score": score,
        "fan_in_unique": int(fan_in_unique),
        "tx_in_count": int(tx_in_count),
        "fan_out_unique": int(fan_out_unique),
        "tx_out_count": int(tx_out_count),
        "recent_sources": recent_sources,
        "recent_dests": recent_dests,
    }

def top_suspects(rds, *, hours: int = 24, limit: int = 10) -> List[Dict]:
    """
    Scanează toate cheile de tip in_sources și calculează scorul curent pentru fiecare IBAN.
    Pentru demo este suficient (date moderate). Dacă devine mare, se poate menține un "leaderboard".
    """
    pattern = f"{PREFIX}:in_sources:*"
    cursor = 0
    ibans = []
    while True:
        cursor, keys = rds.scan(cursor=cursor, match=pattern, count=200)
        for k in keys:
            k_str = k.decode() if isinstance(k, bytes) else k
            ibans.append(k_str.split(":")[-1])
        if cursor == 0:
            break

    # calculează scorul pentru fiecare și sortează
    scored: List[Tuple[int, Dict]] = []
    for iban in set(ibans):
        stats = _stats_for_iban(rds, iban, hours=hours)
        if stats["mule_score"] > 0:
            scored.append((stats["mule_score"], stats))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:limit]]

def stats_for_iban(rds, iban: str, hours: int = 24) -> Dict:
    return _stats_for_iban(rds, iban, hours=hours)
