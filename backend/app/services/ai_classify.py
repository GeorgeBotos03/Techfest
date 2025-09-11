import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from fastapi import APIRouter, Request

import openai

# Încarcă cheia OpenAI din .env din root-ul proiectului
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))
openai.api_key = os.getenv("OPENAI_API_KEY")

router = APIRouter()

LABELS = ["investment", "impersonation", "romance", "invoice", "other", "scam", "safe", "suspicious"]

def classify_payment(features: Dict[str,Any], signals: Dict[str,Any]) -> Dict[str,Any]:
    if not openai.api_key:
        return {"classification": "other", "confidence": 0.5, "explanation": "No LLM key; fallback"}
    prompt = (
        f"Classify the likely scam type for this payment. Allowed labels: {LABELS}.\n"
        "Return JSON: classification (one of the labels), confidence (0..1), explanation (short).\n"
        f"Payment: {json.dumps(features, ensure_ascii=False)}; signals: {json.dumps(signals, ensure_ascii=False)}."
    )
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=128
        )
        result = json.loads(resp.choices[0].message['content'].strip())
        # Asigură-te că există cheia 'classification'
        return {
            "classification": result.get("classification", "other"),
            "confidence": result.get("confidence", 0.5),
            "explanation": result.get("explanation", "")
        }
    except Exception:
        return {"classification": "other", "confidence": 0.5, "explanation": "LLM error"}

@router.post("/ai/classify")
async def ai_classify(request: Request):
    data = await request.json()
    features = data.get("features", {})
    signals = data.get("signals", {})
    result = classify_payment(features, signals)
    return result
