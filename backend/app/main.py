# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict
from fastapi import Body

import csv
import io
from fastapi import FastAPI, Depends, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.orm import Session

# ---- AI services ----
from app.services.ai_explain import ai_explain as _ai_explain
from app.services.ai_classify import classify_payment
# sus, la importuri
from app.services.ai_quiz import generate_quiz, score_quiz_llm


# ---- ML (status, train, predict) ----
from app.ml.model import train_and_save, try_load, predict_proba_one, status as ml_status

# ---- Payment scoring / rules ----
from app.schemas import PaymentIn, ScoreOut, AlertOut, QuizIn, QuizOut
from app.services.quiz import score_quiz
from app.services.watchlist import add_iban, remove_iban, list_ibans, is_watchlisted
from app.services.scoring import score_payment
from app.services.cop_check import confirmation_of_payee

# ---- Mule Radar (Redis) ----
from app.services.mule import record_payment, stats_for_iban, top_suspects

# ---- DB models / deps ----
from app.models import Account, Transaction, Customer

# get_db + get_redis (fallback simplu dacă lipsesc)
try:
    from app.deps import get_db, get_redis
except Exception:  # pragma: no cover
    from app.deps import get_db  # type: ignore
    import os, redis
    def get_redis():
        return redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://redis:6379/0"),
            decode_responses=True
        )

# ------------------------------------------------------------------------------
# App
# ------------------------------------------------------------------------------
app = FastAPI(title="Anti-Scam API")

# ML auto-load la pornire (nu blocăm în caz de eroare)
@app.on_event("startup")
async def _load_ml():
    try:
        try_load()
    except Exception:
        pass

# CORS (pentru Angular dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:43901",
        "http://127.0.0.1:43901",
        "http://127.0.0.1:42105",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# Health / root
# ------------------------------------------------------------------------------
@app.get("/")
def root():
    return {"status": "ok", "health": "/health", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}

# ------------------------------------------------------------------------------
# Score Payment (rules + ML + Mule Radar)
# ------------------------------------------------------------------------------
@app.post("/scorePayment", response_model=ScoreOut)
async def score_payment_endpoint(
    p: PaymentIn,
    db: Session = Depends(get_db),
    r = Depends(get_redis),
):
    # 1) CoP (confirmation of payee)
    provided_name = None
    if p.description and "payee:" in p.description.lower():
        provided_name = p.description.split(":", 1)[1].strip()
    cop_ok, cop_msg = await confirmation_of_payee(p.dst_account_iban, provided_name)

    # 2) Mule Radar: înregistrare + scor
    try:
        record_payment(r, ts_iso=p.ts, src_iban=p.src_account_iban, dst_iban=p.dst_account_iban)
    except Exception:
        pass
    mule_r = 0
    try:
        mule_stats = stats_for_iban(r, p.dst_account_iban, hours=24)
        mule_r = int(mule_stats.get("mule_score", 0))
    except Exception:
        mule_r = 0
    on_watchlist = is_watchlisted(p.dst_account_iban) or mule_r >= 80

    # 3) Feature set
    features: Dict = {
        "amount": p.amount,
        "channel": p.channel,
        "is_first_to_payee": p.is_first_to_payee,
        "description": p.description,
        "src_iban": p.src_account_iban,
        "dst_iban": p.dst_account_iban,
    }

    # 4) Reguli + semnale
    score, action, reasons, cooloff = score_payment(features, cop_ok, on_watchlist)
    if not cop_ok:
        reasons.append(f"CoP: {cop_msg}")
    if mule_r >= 60:
        reasons.append(f"MuleRadar risk={mule_r}")
    if on_watchlist and "Beneficiary on watchlist" not in reasons:
        reasons.append("Beneficiary on watchlist")

    # 5) ML (dacă este model)
    try:
        ml_row = {
            "amount": features.get("amount", 0.0),
            "is_first_to_payee": bool(features.get("is_first_to_payee")),
            "channel": features.get("channel", "web"),
            "description": features.get("description") or "",
        }
        ml_p = predict_proba_one(ml_row)  # None dacă modelul nu e încărcat
        if ml_p is not None:
            reasons.append(f"ML: p_scam={ml_p:.2f}")
            rule_norm = min(float(score) / 100.0, 1.0)
            final = 100.0 * (0.6 * rule_norm + 0.4 * ml_p)
            score = float(final)
            if score >= 60:
                action, cooloff = "hold", 30
            elif score >= 30:
                action, cooloff = "warn", 15
            else:
                action, cooloff = "allow", 0
    except NameError:
        pass

    # 6) Persistență minimă (demo)
    src_acct = db.query(Account).filter(Account.iban == p.src_account_iban).one_or_none()
    if not src_acct:
        cust = db.query(Customer).filter(Customer.external_id == "demo").one_or_none()
        if not cust:
            cust = Customer(external_id="demo", name="Demo User")
            db.add(cust)
            db.flush()
        src_acct = Account(customer_id=cust.id, iban=p.src_account_iban)
        db.add(src_acct)
        db.flush()

    dst_acct = db.query(Account).filter(Account.iban == p.dst_account_iban).one_or_none()
    dst_account_id = dst_acct.id if dst_acct else None

    txn = Transaction(
        ts=p.ts,
        src_account_id=src_acct.id,
        dst_account_id=dst_account_id,
        dst_iban=p.dst_account_iban,
        amount_cents=int(round(p.amount * 100)),
        currency=p.currency,
        channel=p.channel,
        is_first_to_payee=p.is_first_to_payee,
        device_fp=p.device_fp,
        risk_score=score,
        risk_reasons=reasons,
        action=action,
    )
    db.add(txn)
    db.commit()

    return ScoreOut(risk_score=score, action=action, reasons=reasons, cooloff_minutes=cooloff)

# ------------------------------------------------------------------------------
# Alerts (list + decision)
# ------------------------------------------------------------------------------
@app.get("/alerts", response_model=List[AlertOut])
def list_alerts(
    db: Session = Depends(get_db),
    action: Optional[str] = Query(None, description="warn|hold"),
    dst_iban: Optional[str] = Query(None, description="destination IBAN (contains)"),
    since: Optional[str] = Query(None, description="ISO datetime"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    q = select(Transaction).where(Transaction.action != "allow")
    if action in {"warn", "hold"}:
        q = q.where(Transaction.action == action)
    if dst_iban:
        q = q.where(Transaction.dst_iban.ilike(f"%{dst_iban}%"))
    if since:
        try:
            ts = datetime.fromisoformat(since.replace("Z", "+00:00"))
            q = q.where(Transaction.ts >= ts)
        except Exception:
            pass

    q = q.order_by(Transaction.id.desc()).offset(offset).limit(limit)
    rows = db.execute(q).scalars().all()

    account_ids = {r.src_account_id for r in rows if r.src_account_id} | {r.dst_account_id for r in rows if r.dst_account_id}
    id_to_iban: Dict[int, str] = {}
    if account_ids:
        accts = db.query(Account).filter(Account.id.in_(account_ids)).all()
        id_to_iban = {a.id: a.iban for a in accts}

    out: List[AlertOut] = []
    for r in rows:
        out.append(AlertOut(
            id=int(r.id),
            ts=r.ts,
            src_account_iban=id_to_iban.get(r.src_account_id),
            dst_account_iban=r.dst_iban or id_to_iban.get(r.dst_account_id),
            amount=float(r.amount_cents) / 100.0,
            currency=r.currency,
            channel=r.channel,
            action=r.action,
            reasons=list(r.risk_reasons or []),
        ))
    return out

@app.post("/alerts/{alert_id}/decision")
def decide_alert(alert_id: int, decision: str, db: Session = Depends(get_db)):
    if decision not in {"release", "cancel"}:
        raise HTTPException(status_code=400, detail="decision must be release|cancel")
    txn = db.query(Transaction).filter(Transaction.id == alert_id).one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="alert not found")
    txn.action = "allow" if decision == "release" else "hold"
    db.commit()
    return {"ok": True, "id": alert_id, "new_action": txn.action}

# ------------------------------------------------------------------------------
# Stats
# ------------------------------------------------------------------------------
@app.get("/stats")
def stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Transaction.id)).scalar() or 0
    by_action = dict(db.query(Transaction.action, func.count(Transaction.id)).group_by(Transaction.action).all())
    prevented_cents = db.query(func.coalesce(func.sum(Transaction.amount_cents), 0)) \
                        .filter(Transaction.action == "hold").scalar() or 0
    return {
        "total_tx": int(total),
        "by_action": {k: int(v) for k, v in by_action.items()},
        "percent": {k: (int(v) / total * 100.0 if total else 0.0) for k, v in by_action.items()},
        "losses_prevented_RON": round(prevented_cents / 100.0, 2),
    }

# ------------------------------------------------------------------------------
# Dynamic Friction Quiz
# ------------------------------------------------------------------------------
@app.post("/quiz/{alert_id}", response_model=QuizOut)
def quiz_decision(alert_id: int, q: QuizIn, db: Session = Depends(get_db)):
    txn = db.query(Transaction).filter(Transaction.id == alert_id).one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="alert not found")

    prev = txn.action
    score, decision, reasons = score_quiz(q)
    if decision == "release":
        txn.action = "allow"
    elif decision == "warn":
        txn.action = "warn"
    else:
        txn.action = "hold"

    db.commit()
    return QuizOut(id=int(txn.id), previous_action=prev, new_action=txn.action, score=score, reasons=reasons)

# ------------------------------------------------------------------------------
# Watchlist admin
# ------------------------------------------------------------------------------
@app.get("/watchlist")
def get_watchlist():
    return {"ibans": list_ibans()}

@app.post("/watchlist/add")
def add_watchlist(iban: str):
    add_iban(iban)
    return {"ok": True, "ibans": list_ibans()}

@app.post("/watchlist/remove")
def remove_watchlist(iban: str):
    remove_iban(iban)
    return {"ok": True, "ibans": list_ibans()}

# ------------------------------------------------------------------------------
# Alerts export CSV
# ------------------------------------------------------------------------------
@app.get("/alerts/export.csv")
def export_alerts_csv(
    db: Session = Depends(get_db),
    action: Optional[str] = Query(None, description="warn|hold"),
    since: Optional[str] = Query(None, description="ISO datetime"),
):
    q = select(Transaction).where(Transaction.action != "allow")
    if action in {"warn", "hold"}:
        q = q.where(Transaction.action == action)
    if since:
        try:
            ts = datetime.fromisoformat(since.replace("Z", "+00:00"))
            q = q.where(Transaction.ts >= ts)
        except Exception:
            pass
    q = q.order_by(Transaction.id.desc()).limit(10_000)
    rows = db.execute(q).scalars().all()

    account_ids = {r.src_account_id for r in rows if r.src_account_id} | {r.dst_account_id for r in rows if r.dst_account_id}
    id_to_iban: Dict[int, str] = {}
    if account_ids:
        accts = db.query(Account).filter(Account.id.in_(account_ids)).all()
        id_to_iban = {a.id: a.iban for a in accts}

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id","ts","src_iban","dst_iban","amount_RON","currency","channel","action","reasons"])
    for r in rows:
        w.writerow([
            int(r.id),
            r.ts.isoformat() if r.ts else "",
            id_to_iban.get(r.src_account_id, ""),
            r.dst_iban or id_to_iban.get(r.dst_account_id, ""),
            f"{float(r.amount_cents)/100.0:.2f}",
            r.currency,
            r.channel,
            r.action,
            "; ".join(r.risk_reasons or []),
        ])
    buf.seek(0)
    return StreamingResponse(buf, media_type="text/csv", headers={
        "Content-Disposition": 'attachment; filename="alerts.csv"'
    })

# ------------------------------------------------------------------------------
# ML endpoints
# ------------------------------------------------------------------------------
@app.post("/ml/train")
def ml_train(n: int = Query(3000, ge=500, le=50000), scam_ratio: float = Query(0.5, ge=0.1, le=0.9), seed: int = 42):
    meta = train_and_save(n=n, scam_ratio=scam_ratio, seed=seed)
    return {"ok": True, "meta": meta}

@app.get("/ml/status")
def ml_status_route():
    return ml_status()

# ------------------------------------------------------------------------------
# Mule Radar endpoints
# ------------------------------------------------------------------------------
@app.get("/mule/{iban}")
def mule_one(iban: str, hours: int = Query(24, ge=1, le=168), r = Depends(get_redis)):
    return stats_for_iban(r, iban, hours=hours)

@app.get("/mule/top")
def mule_top(hours: int = Query(24, ge=1, le=168), limit: int = Query(10, ge=1, le=50), r = Depends(get_redis)):
    return top_suspects(r, hours=hours, limit=limit)

# ------------------------------------------------------------------------------
# AI endpoints (EXPLAIN / CLASSIFY) – robuste, cu fallback JSON
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# AI endpoints (EXPLAIN / QUIZ / CLASSIFY) – robuste, cu fallback JSON
# ------------------------------------------------------------------------------
@app.post("/ai/explain")
def ai_explain_endpoint(payload: dict = Body(...)):
    # extragem în siguranță parametrii
    features = {}
    signals = {}
    try:
        features = payload.get("features") or {}
        signals  = payload.get("signals") or {}
    except Exception:
        pass

    try:
        out = _ai_explain(features, signals)  # <- apel standard (features, signals)
        # normalizăm cheile înainte de return
        return {
            "summary": out.get("summary", "Potential scam indicators detected."),
            "key_reasons": out.get("key_reasons", []),
            "recommendations": out.get("recommendations", []),
        }
    except Exception as e:
        print("ai_explain_endpoint ERROR:", repr(e))
        # fallback final – UI-ul rămâne funcțional
        return {
            "summary": "AI fallback (error)",
            "key_reasons": [],
            "recommendations": [
                "Verify recipient via official channels.",
                "Avoid urgency pressure.",
                "Double-check invoice details."
            ],
        }
@app.post("/ai/quiz")
def ai_quiz(payload: dict = Body(...)):
    """Generează întrebări dinamice (LLM dacă e cheie, altfel fallback)."""
    try:
        signals = payload.get("signals") or {}
    except Exception:
        signals = {}
    try:
        return generate_quiz(signals)
    except Exception as e:
        print("ai_quiz ERROR:", repr(e))
        # fallback minimalist
        return {
            "questions": ["Are you being pressured to act quickly?"],
            "rubric": ["Urgency pressure is a common scam tactic."]
        }

@app.post("/ai/quiz/score")
def ai_quiz_score(payload: dict = Body(...)):
    """Evaluează răspunsurile (LLM dacă e cheie, altfel fallback)."""
    try:
        questions = payload.get("questions") or []
        answers   = payload.get("answers") or []
    except Exception:
        questions, answers = [], []
    try:
        score, decision, reasons = score_quiz_llm(questions, answers)
        return {"score": score, "decision": decision, "reasons": reasons}
    except Exception as e:
        print("ai_quiz_score ERROR:", repr(e))
        # fallback simplu
        return {"score": 0, "decision": "warn", "reasons": ["Unable to evaluate quiz."]}
        
@app.post("/ai/classify")
def ai_classify(payload: dict = Body(...)):
    try:
        features = payload.get("features") or {}
        signals  = payload.get("signals") or {}
    except Exception:
        features, signals = {}, {}
    try:
        return classify_payment(features, signals)
    except Exception as e:
        print("ai_classify ERROR:", repr(e))
        return {"classification": "unknown"}
