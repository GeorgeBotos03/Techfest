# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Dict

import csv, io
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func

# ---- ML (status, train, predict) ----
from app.ml.model import train_and_save, try_load, predict_proba_one, status as ml_status

# ---- Schemas / services existente ----
from app.schemas import PaymentIn, ScoreOut, AlertOut, QuizIn, QuizOut
from app.services.quiz import score_quiz
from app.services.watchlist import add_iban, remove_iban, list_ibans, is_watchlisted
from app.services.scoring import score_payment
from app.services.cop_check import confirmation_of_payee

# ---- Mule Radar (nou) ----
from app.services.mule import record_payment, stats_for_iban, top_suspects

# ---- DB models / deps ----
from app.models import Account, Transaction, Customer

# get_db + get_redis (cu fallback dacă nu e implementat)
try:
    from app.deps import get_db, get_redis
except Exception:
    # avem get_db, dar poate nu e definit get_redis: furnizăm un fallback simplu
    from app.deps import get_db  # type: ignore
    import os, redis
    def get_redis():
        return redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)

app = FastAPI(title="Anti-Scam API")

# ---- ML auto-load la startup ----
@app.on_event("startup")
async def _load_ml():
    try_load()

# ---- CORS pentru Angular (4200) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Health / Root ----------
@app.get("/")
def root():
    return {"status": "ok", "health": "/health", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}

# ---------- Score Payment (reguli + ML + Mule Radar) ----------
@app.post("/scorePayment", response_model=ScoreOut)
async def score_payment_endpoint(
    p: PaymentIn,
    db: Session = Depends(get_db),
    r = Depends(get_redis),
):
    # 1) CoP (Confirmation of Payee) – extragem un nume din description dacă e cazul
    provided_name = None
    if p.description and "payee:" in p.description.lower():
        provided_name = p.description.split(":", 1)[1].strip()
    cop_ok, cop_msg = await confirmation_of_payee(p.dst_account_iban, provided_name)

    # 2) Mule Radar – înregistrăm tranzacția în graf (fan-in/out) și citim scorul curent
    try:
        record_payment(r, ts_iso=p.ts, src_iban=p.src_account_iban, dst_iban=p.dst_account_iban)
    except Exception:
        # nu blocăm flow-ul dacă Redis are probleme
        pass

    mule_stats = {}
    mule_r = 0
    try:
        mule_stats = stats_for_iban(r, p.dst_account_iban, hours=24)
        mule_r = int(mule_stats.get("mule_score", 0))
    except Exception:
        mule_r = 0

    # Watchlist dinamic pe baza Mule Radar + watchlist manual
    on_watchlist = is_watchlisted(p.dst_account_iban) or mule_r >= 80  # prag simplu pentru demo

    # 3) Features pentru scorare pe reguli
    features: Dict = {
        "amount": p.amount,
        "channel": p.channel,
        "is_first_to_payee": p.is_first_to_payee,
        "description": p.description,
        "src_iban": p.src_account_iban,
        "dst_iban": p.dst_account_iban,
    }

    # 4) Scorare pe reguli + semnale
    score, action, reasons, cooloff = score_payment(features, cop_ok, on_watchlist)

    if not cop_ok:
        reasons.append(f"CoP: {cop_msg}")
    if mule_r >= 60:
        reasons.append(f"MuleRadar risk={mule_r}")
    if on_watchlist and "Beneficiary on watchlist" not in reasons:
        reasons.append("Beneficiary on watchlist")

    # 5) Integrare ML (dacă modelul e încărcat)
    try:
        ml_row = {
            "amount": features.get("amount", 0.0),
            "is_first_to_payee": bool(features.get("is_first_to_payee")),
            "channel": features.get("channel", "web"),
            "description": features.get("description") or "",
        }
        ml_p = predict_proba_one(ml_row)  # None dacă nu e încărcat
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
        # dacă nu avem importul predict_proba_one, ignorăm ML
        pass

    # 6) Persistență minimă a tranzacției
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

# ---------- Alerts (list + decision) ----------
@app.get("/alerts", response_model=List[AlertOut])
def list_alerts(
    db: Session = Depends(get_db),
    action: Optional[str] = Query(None, description="filter by action: warn|hold"),
    dst_iban: Optional[str] = Query(None, description="filter by destination IBAN (contains)"),
    since: Optional[str] = Query(None, description="ISO datetime, return alerts since this moment"),
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

    # mapare id -> IBAN
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

# ---------- Stats ----------
@app.get("/stats")
def stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Transaction.id)).scalar() or 0
    by_action = dict(db.query(Transaction.action, func.count(Transaction.id)).group_by(Transaction.action).all())
    prevented_cents = db.query(func.coalesce(func.sum(Transaction.amount_cents), 0)) \
                        .filter(Transaction.action == "hold").scalar() or 0

    resp = {
        "total_tx": int(total),
        "by_action": {k: int(v) for k, v in by_action.items()},
        "percent": {k: (int(v) / total * 100.0 if total else 0.0) for k, v in by_action.items()},
        "losses_prevented_RON": round(prevented_cents / 100.0, 2),
    }
    return resp

# ---------- Dynamic Friction Quiz ----------
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
    else:  # "cancel"
        txn.action = "hold"

    db.commit()
    return QuizOut(id=int(txn.id), previous_action=prev, new_action=txn.action, score=score, reasons=reasons)

# ---------- Watchlist admin ----------
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

# ---------- Alerts export CSV ----------
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

    # mapare IBAN
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

# ---------- ML endpoints ----------
@app.post("/ml/train")
def ml_train(n: int = Query(3000, ge=500, le=50000), scam_ratio: float = Query(0.5, ge=0.1, le=0.9), seed: int = 42):
    meta = train_and_save(n=n, scam_ratio=scam_ratio, seed=seed)
    return {"ok": True, "meta": meta}

@app.get("/ml/status")
def ml_status_route():
    return ml_status()

# ---------- Mule Radar endpoints ----------
@app.get("/mule/{iban}")
def mule_one(iban: str, hours: int = Query(24, ge=1, le=168), r = Depends(get_redis)):
    """
    Statistici Mule pentru un IBAN (ultimele `hours` ore).
    """
    return stats_for_iban(r, iban, hours=hours)

@app.get("/mule/top")
def mule_top(hours: int = Query(24, ge=1, le=168), limit: int = Query(10, ge=1, le=50), r = Depends(get_redis)):
    """
    Top IBAN-uri suspecte ca destinație în fereastra recentă.
    """
    return top_suspects(r, hours=hours, limit=limit)
