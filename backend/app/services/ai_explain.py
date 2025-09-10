# backend/app/services/ai_explain.py
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Tuple

from .ai_client import get_openai_client  # trebuie să returneze (client_or_None, model_name)

log = logging.getLogger(__name__)


def _sanitize(features: Dict[str, Any]) -> Dict[str, Any]:
    """Nu trimitem IBAN-urile complet și tăiem câmpuri lungi."""
    f = dict(features)
    for k in ("src_account_iban", "dst_account_iban"):
        v = f.get(k)
        if isinstance(v, str) and len(v) > 8:
            f[k] = f"{v[:2]}…{v[-4:]}"
    # scurtăm descrierea pentru prompt
    if isinstance(f.get("description"), str) and len(f["description"]) > 240:
        f["description"] = f["description"][:240] + "…"
    return f


def _fallback(features: Dict[str, Any], signals: Dict[str, Any]) -> Dict[str, Any]:
    """Explicație deterministică atunci când LLM nu e disponibil."""
    reasons: List[str] = []
    if not signals.get("cop_ok", True):
        reasons.append("Recipient name mismatch (CoP failed)")
    mule = signals.get("mule_score", 0)
    if isinstance(mule, (int, float)) and mule >= 80:
        reasons.append(f"High mule risk ({mule})")
    if signals.get("watchlisted"):
        reasons.append("Recipient on bank watchlist")
    mlp = signals.get("ml_p")
    if isinstance(mlp, (int, float)):
        reasons.append(f"Model p(scam) ≈ {mlp:.0%}")
    if not reasons:
        reasons.append("No strong scam indicators")

    tips = [
        "Verify the recipient via official channels (do not trust numbers from messages).",
        "Do not proceed if pressured for urgency or secrecy.",
        "If investment-related: check license/company in the official register.",
    ]
    return {"summary": reasons[0], "key_reasons": reasons[:4], "recommendations": tips}


def _ensure_shape(d: Dict[str, Any]) -> Dict[str, Any]:
    """Ne asigurăm că răspunsul are cheile așteptate."""
    return {
        "summary": d.get("summary") or "Potential scam indicators detected.",
        "key_reasons": list(d.get("key_reasons") or []),
        "recommendations": list(d.get("recommendations") or []),
    }


def ai_explain(features: Dict[str, Any], signals: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generează o explicație scurtă pentru risc de scam folosind un LLM (dacă e disponibil),
    altfel revine la fallback bazat pe reguli/semnale.
    """
    client, model = get_openai_client()  # -> Tuple[OpenAI|None, str]
    if not client:
        return _fallback(features, signals)

    sys = (
        "You are a banking scam-prevention assistant. "
        "Analyze the transaction and return a STRICT JSON with exactly these keys: "
        "`summary` (short string), `key_reasons` (array of up to 4 short strings), "
        "`recommendations` (array of 3 concise actions). "
        "No extra keys, no prose, JSON only."
    )
    user = f"Signals: {json.dumps(signals, ensure_ascii=False)}\n" \
           f"Payment: {json.dumps(_sanitize(features), ensure_ascii=False)}"

    try:
        # OpenAI responses with a JSON object (uses response_format when available)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": sys},
                      {"role": "user", "content": user}],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = (resp.choices[0].message.content or "").strip()
        data = json.loads(content)
        return _ensure_shape(data)

    except Exception as e:
        # Logăm, dar nu dăm fail spre UI
        log.warning("ai_explain: LLM failed, using fallback. err=%s", e)
        return _fallback(features, signals)
