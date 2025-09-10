# backend/app/services/ai_client.py
from __future__ import annotations

import os
import json
from typing import Any, Dict, Optional, Tuple

# Config din env
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

_client: Optional[Any] = None

# Inițializare client OpenAI (opțional; dacă lipsește cheia facem fallback)
try:
    if OPENAI_API_KEY:
        from openai import OpenAI
        _client = OpenAI(api_key=OPENAI_API_KEY)
except Exception:
    _client = None  # nu cădem; lăsăm fallback pe stratul superior


def get_openai_client() -> Tuple[Optional[Any], str]:
    """
    Returnează (client_or_None, model_name).
    Dacă clientul e None, stratul care consumă va face fallback deterministic.
    """
    return _client, OPENAI_MODEL


def explain_with_llm(features: Dict[str, Any], signals: Dict[str, Any]) -> Dict[str, Any]:
    """
    Utilitar simplu (opțional) dacă vrei să întrebi direct LLM-ul de aici.
    Întoarce dict {summary, key_reasons, recommendations}.
    Dacă nu există client sau apare o eroare -> fallback deterministic.
    """
    # Fallback determinist (sigur pentru UI)
    fallback = {
        "summary": "Potential scam indicators detected.",
        "key_reasons": [],
        "recommendations": [
            "Verify recipient via official channels.",
            "Do not proceed under urgency pressure.",
            "Avoid sending funds to unknown crypto wallets."
        ],
    }
    # Motive de bază extrase din semnale
    try:
        if not signals.get("cop_ok", True):
            fallback["key_reasons"].append("Confirmation of Payee mismatch")
        mule = signals.get("mule_score", 0)
        if isinstance(mule, (int, float)) and mule >= 80:
            fallback["key_reasons"].append(f"High mule risk ({mule})")
        if signals.get("watchlisted"):
            fallback["key_reasons"].append("Recipient on watchlist")
        mlp = signals.get("ml_p")
        if isinstance(mlp, (int, float)):
            fallback["key_reasons"].append(f"Model p(scam) ≈ {mlp:.0%}")
    except Exception:
        pass

    if _client is None:
        return fallback

    try:
        sys = (
            "You are a banking scam-prevention assistant. "
            "Analyze the transaction and return a STRICT JSON with keys: "
            "`summary` (short string), `key_reasons` (array of up to 4 short strings), "
            "`recommendations` (array of 3 concise actions). No extra keys."
        )
        user = "Features:\n" + json.dumps(features, ensure_ascii=False) + \
               "\nSignals:\n" + json.dumps(signals, ensure_ascii=False)

        resp = _client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "system", "content": sys},
                      {"role": "user", "content": user}],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = (resp.choices[0].message.content or "").strip()
        out = json.loads(content)
        if not isinstance(out, dict) or "summary" not in out:
            raise ValueError("Unexpected JSON shape")
        return {
            "summary": out.get("summary", fallback["summary"]),
            "key_reasons": out.get("key_reasons", []) or fallback["key_reasons"],
            "recommendations": out.get("recommendations", []) or fallback["recommendations"],
        }
    except Exception:
        return fallback
