from typing import Dict, Any, List, Tuple
from .ai_client import get_openai_client

def quiz_fallback(signals: Dict[str,Any]) -> Dict[str, Any]:
    # 3 întrebări de bază + rubric simplă
    return {
        "questions": [
            "Did someone ask you to keep this payment secret or act urgently?",
            "Did you verify the recipient using an official phone/website?",
            "Is this payment related to investment/crypto or a refund/overpayment?"
        ],
        "rubric": [
            "If Q1=yes -> strong risk",
            "If Q2=no -> medium risk",
            "If Q3=yes -> medium risk"
        ]
    }

def generate_quiz(signals: Dict[str, Any]) -> Dict[str, Any]:
    client, model = get_openai_client()
    if not client:
        return quiz_fallback(signals)
    prompt = f"""
Generate 3-5 short questions to help prevent bank transfer scams, based on these signals:
{signals}
Return JSON: questions (array of strings), rubric (array of scoring rules in plain text).
Keep questions short and neutral.
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
        return quiz_fallback(signals)

def score_quiz_llm(questions: List[str], answers: List[str]) -> Tuple[int,str,List[str]]:
    client, model = get_openai_client()
    if not client:
        # scor simplu fallback
        score = 0
        if any(a.strip().lower() in {"yes","da"} for a in answers[:1]): score += 70
        if len(answers)>1 and answers[1].strip().lower() in {"no","nu"}: score += 30
        decision = "cancel" if score>=70 else "warn" if score>=30 else "release"
        return score, decision, ["Heuristic scoring (no LLM)"]
    prompt = f"""
We asked the user these questions: {questions}
They answered: {answers}
Give a JSON: score (0-100), decision (release|warn|cancel), reasons (array).
Focus on scam-prevention risk.
"""
    import json
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role":"user","content":prompt}],
            response_format={"type":"json_object"},
            temperature=0.1,
        )
        data = json.loads(resp.choices[0].message.content)
        return int(data.get("score",0)), data.get("decision","warn"), data.get("reasons",[])
    except Exception:
        return 50, "warn", ["LLM error; default warn"]
