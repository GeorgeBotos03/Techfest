from typing import Dict, Any
from .ai_client import get_openai_client

LABELS = ["investment", "impersonation", "romance", "invoice", "other"]

def classify_payment(features: Dict[str,Any], signals: Dict[str,Any]) -> Dict[str,Any]:
    client, model = get_openai_client()
    if not client:
        return {"label":"other", "confidence":0.5, "explanation":"No LLM key; fallback"}
    prompt = f"""
Classify the likely scam type for this payment. Allowed labels: {LABELS}.
Return JSON: label (one of {LABELS}), confidence (0..1), explanation (short).
Payment: {features}; signals: {signals}.
"""
    import json
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role":"user","content":prompt}],
            response_format={"type":"json_object"},
            temperature=0.2,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return {"label":"other", "confidence":0.5, "explanation":"LLM error"}
