from typing import Dict, Any, List
from .ai_client import get_openai_client

def _sanitize(features: Dict[str, Any]) -> Dict[str, Any]:
    # NU trimitem IBANuri complete; doar ultimele 4 caractere
    f = dict(features)
    for k in ["src_account_iban", "dst_account_iban"]:
        v = f.get(k)
        if isinstance(v, str) and len(v) > 8:
            f[k] = f"{v[:2]}…{v[-4:]}"
    return f

def explain_fallback(features: Dict[str, Any], signals: Dict[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    if not signals.get("cop_ok", True): reasons.append("Recipient name mismatch (CoP failed)")
    mule = signals.get("mule_score", 0)
    if mule >= 80: reasons.append(f"High mule risk ({mule})")
    if signals.get("watchlisted"): reasons.append("Recipient on bank watchlist")
    mlp = signals.get("ml_p")
    if mlp is not None: reasons.append(f"Model p(scam) ≈ {mlp:.0%}")
    if not reasons: reasons.append("No strong scam indicators")
    tips = [
        "Call the recipient via an official number; do not trust numbers from messages.",
        "Do not proceed if pressured for urgency or secrecy.",
        "If investment: verify the license/company on the official register."
    ]
    return {"summary": reasons[0], "key_reasons": reasons[:4], "recommendations": tips}

def ai_explain(features: Dict[str, Any], signals: Dict[str, Any]) -> Dict[str, Any]:
    client, model = get_openai_client()
    if not client:
        return explain_fallback(features, signals)
    prompt = f"""
You are a banking scam-prevention assistant. Summarize the scam risk for this payment (JSON).
Return fields: summary (short), key_reasons (array, up to 4), recommendations (3 concise actions).
Signals: {signals}. Payment: {_sanitize(features)}.
"""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role":"user","content":prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        import json
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return explain_fallback(features, signals)
