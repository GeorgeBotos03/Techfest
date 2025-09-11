# app/services/ai_quiz.py
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from .ai_client import get_openai_client  # -> (client_or_None, model_name)


# ----------------- Helpers & fallback -----------------

def _quiz_fallback(signals: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback deterministic: 3 întrebări scurte + rubric simplă.
    """
    return {
        "questions": [
            "Were you asked to act urgently or keep this payment secret?",
            "Have you verified the recipient via an official website or phone number?",
            "Is this payment related to investments, crypto, refunds or overpayments?"
        ],
        "rubric": [
            "Q1 = yes → strong risk indicator",
            "Q2 = no  → medium risk indicator",
            "Q3 = yes → medium risk indicator"
        ],
    }


def _ensure_quiz_shape(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Asigură forma: {"questions": [str..], "rubric": [str..]}
    """
    out_q = d.get("questions") or []
    out_r = d.get("rubric") or []
    if not isinstance(out_q, list):
        out_q = []
    if not isinstance(out_r, list):
        out_r = []
    # păstrează doar stringuri
    out_q = [str(x) for x in out_q][:5]
    out_r = [str(x) for x in out_r][:8]
    # minim 3 întrebări
    if len(out_q) < 3:
        out_q = _quiz_fallback({})["questions"]
    return {"questions": out_q, "rubric": out_r}


def _ensure_score_shape(d: Dict[str, Any]) -> Tuple[int, str, List[str]]:
    """
    Normalizează răspunsul de scor: (score 0..100, decision, reasons[])
    """
    try:
        score = int(d.get("score", 0))
    except Exception:
        score = 0
    score = max(0, min(100, score))

    decision = str(d.get("decision", "warn")).lower()
    if decision not in {"release", "warn", "cancel"}:
        decision = "warn"

    reasons = d.get("reasons") or []
    if not isinstance(reasons, list):
        reasons = [str(reasons)]
    reasons = [str(r) for r in reasons][:6]

    return score, decision, reasons


# ----------------- Public API -----------------

def generate_quiz(signals: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generează 3–5 întrebări scurte pentru verificare anti-scam.
    Întoarce {"questions": [...], "rubric": [...]}. Fallback dacă LLM nu e disponibil.
    """
    client, model = get_openai_client()
    if not client:
        return _quiz_fallback(signals)

    sys = (
        "You are a banking scam-prevention assistant. "
        "Generate concise verification questions (3–5) that help detect scam patterns "
        "for a bank transfer. Output STRICT JSON with keys: "
        "`questions` (array of short strings), `rubric` (array of brief scoring rules). "
        "No extra keys, JSON only."
    )
    user = "Signals: " + json.dumps(signals, ensure_ascii=False)

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": sys},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = (resp.choices[0].message.content or "").strip()
        data = json.loads(content)
        return _ensure_quiz_shape(data)
    except Exception:
        return _quiz_fallback(signals)


def score_quiz_llm(questions: List[str], answers: List[str]) -> Tuple[int, str, List[str]]:
    """
    Evaluează răspunsurile la quiz. Întoarce (score 0..100, decision release|warn|cancel, reasons[]).
    Fallback determinist dacă LLM nu e disponibil.
    """
    client, model = get_openai_client()
    if not client:
        # Heuristică simplă (fallback):
        yes1 = 1 if answers[:1] and str(answers[0]).strip().lower() in {"yes", "da"} else 0
        no2  = 1 if len(answers) > 1 and str(answers[1]).strip().lower() in {"no", "nu"} else 0
        yes3 = 1 if len(answers) > 2 and str(answers[2]).strip().lower() in {"yes", "da"} else 0
        score = 70 * yes1 + 20 * yes3 + 10 * no2  # 0..100
        if score >= 70:
            decision = "cancel"
        elif score >= 30:
            decision = "warn"
        else:
            decision = "release"
        return score, decision, ["Heuristic scoring (no LLM)"]

    sys = (
        "You are a banking scam-prevention assistant. "
        "Given the user's answers to verification questions, produce STRICT JSON with keys: "
        "`score` (0..100, higher = higher scam risk), "
        "`decision` (one of: release|warn|cancel), "
        "`reasons` (array of short strings). JSON only."
    )
    user = (
        "Questions: " + json.dumps(questions, ensure_ascii=False) + "\n"
        "Answers: " + json.dumps(answers, ensure_ascii=False)
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": sys},
                {"role": "user", "content": user},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        content = (resp.choices[0].message.content or "").strip()
        data = json.loads(content)
        return _ensure_score_shape(data)
    except Exception:
        return 50, "warn", ["LLM error; default warn"]
