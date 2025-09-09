<<<<<<< HEAD
from fastapi import FastAPI, Depends, HTTPException
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import select

from app.schemas import PaymentIn, ScoreOut, AlertOut
from app.deps import get_db
from app.models import Account, Transaction, Customer

# stubs simple pentru demo (evităm importuri lipsă)
async def score_payment(features, cop_ok, on_watchlist):
    score = 0; reasons=[]
    if features.get("amount",0) >= 5000: score+=40; reasons.append("High amount")
    if features.get("is_first_to_payee"): score+=25; reasons.append("First payment to beneficiary")
    if features.get("channel")=="mobile": score+=15; reasons.append("Mobile channel")
    if not cop_ok: score+=30; reasons.append("CoP mismatch")
    if on_watchlist: score+=60; reasons.append("Watchlist hit")
    action = "allow" if score<40 else ("warn" if score<70 else "hold")
    return float(score), action, reasons, 30 if action!="allow" else 0

async def confirmation_of_payee(iban, provided_name):
    if not provided_name: return True, "no payee name provided"
    ok = "invest" in provided_name.lower()
    return ok, "match" if ok else "mismatch"

def update_graph(src,dst,amount): pass
def mule_risk(iban): return 95 if iban=="RO49AAAA1B31007593840000" else 10
=======
from datetime import datetime
from typing import List, Optional

from datetime import datetime, timezone
import csv, io
from fastapi.responses import StreamingResponse
from fastapi import Query
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.schemas import PaymentIn, ScoreOut, AlertOut, QuizIn, QuizOut
from app.services.quiz import score_quiz
from app.services.watchlist import add_iban, remove_iban, list_ibans, is_watchlisted
from app.services.scoring import score_payment
from app.services.cop_check import confirmation_of_payee
from app.services.mule_graph import update_graph, mule_risk
from app.deps import get_db
from app.models import Account, Transaction, Customer
>>>>>>> origin/main

app = FastAPI(title="Anti-Scam API")

# CORS pentru Angular la 4200
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "health": "/health", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}


@app.post("/scorePayment", response_model=ScoreOut)
async def score_payment_endpoint(p: PaymentIn, db: Session = Depends(get_db)):
<<<<<<< HEAD
=======
    # 1) CoP (confirmation of payee) – extrage nume din descriere "payee: <nume>"
>>>>>>> origin/main
    provided_name = None
    if p.description and "payee:" in p.description.lower():
        provided_name = p.description.split(":", 1)[1].strip()
    cop_ok, cop_msg = await confirmation_of_payee(p.dst_account_iban, provided_name)
<<<<<<< HEAD
=======

    # 2) Mule Radar (grafic)
>>>>>>> origin/main
    update_graph(p.src_account_iban, p.dst_account_iban, p.amount)
    mule_r = mule_risk(p.dst_account_iban)
    on_watchlist = is_watchlisted(p.dst_account_iban) or mule_r >= 80
      # prag simplu

<<<<<<< HEAD
    features = {"amount": p.amount, "channel": p.channel, "is_first_to_payee": p.is_first_to_payee}
    score, action, reasons, cooloff = await score_payment(features, cop_ok, on_watchlist)

    if not cop_ok: reasons.append(f"CoP: {cop_msg}")
    if mule_r >= 60: reasons.append(f"MuleRadar risk={mule_r}")
    if on_watchlist: reasons.append("Beneficiary on watchlist")

    # persist minimal
=======
    # 3) Feature set pentru scor
    features = {
        "amount": p.amount,
        "channel": p.channel,
        "is_first_to_payee": p.is_first_to_payee,
        "description": p.description,
        "src_iban": p.src_account_iban,   # pentru velocity
        "dst_iban": p.dst_account_iban,   # pentru velocity
    }

    # 4) Scorare pe reguli + semnale scam (text + velocity)
    score, action, reasons, cooloff = score_payment(features, cop_ok, on_watchlist)

    if not cop_ok:
        reasons.append(f"CoP: {cop_msg}")
    if mule_r >= 60:
        reasons.append(f"MuleRadar risk={mule_r}")
    if on_watchlist:
        reasons.append("Beneficiary on watchlist")

    # 5) Persistență minimă
>>>>>>> origin/main
    src_acct = db.query(Account).filter(Account.iban == p.src_account_iban).one_or_none()
    if not src_acct:
        cust = db.query(Customer).filter(Customer.external_id == "demo").one_or_none()
        if not cust:
<<<<<<< HEAD
            cust = Customer(external_id="demo", name="Demo User"); db.add(cust); db.flush()
        src_acct = Account(customer_id=cust.id, iban=p.src_account_iban); db.add(src_acct); db.flush()
=======
            cust = Customer(external_id="demo", name="Demo User")
            db.add(cust)
            db.flush()
        src_acct = Account(customer_id=cust.id, iban=p.src_account_iban)
        db.add(src_acct)
        db.flush()
>>>>>>> origin/main

    dst_acct = db.query(Account).filter(Account.iban == p.dst_account_iban).one_or_none()
    dst_account_id = dst_acct.id if dst_acct else None

    txn = Transaction(
<<<<<<< HEAD
        ts=p.ts, src_account_id=src_acct.id, dst_account_id=dst_account_id, dst_iban=p.dst_account_iban,
        amount_cents=int(round(p.amount * 100)), currency=p.currency, channel=p.channel,
        is_first_to_payee=p.is_first_to_payee, device_fp=p.device_fp,
        risk_score=score, risk_reasons=reasons, action=action,
    )
    db.add(txn); db.commit()

    return ScoreOut(risk_score=score, action=action, reasons=reasons, cooloff_minutes=cooloff)

@app.get("/alerts", response_model=List[AlertOut])
def list_alerts(db: Session = Depends(get_db)):
    q = select(Transaction).where(Transaction.action != "allow").order_by(Transaction.id.desc()).limit(200)
    rows = db.execute(q).scalars().all()

=======
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
        # acceptăm ISO 8601; dacă nu e valid, ignorăm
        try:
            ts = datetime.fromisoformat(since.replace("Z", "+00:00"))
            q = q.where(Transaction.ts >= ts)
        except Exception:
            pass

    q = q.order_by(Transaction.id.desc()).offset(offset).limit(limit)
    rows = db.execute(q).scalars().all()

    # mapare id->iban
>>>>>>> origin/main
    account_ids = {r.src_account_id for r in rows if r.src_account_id} | {r.dst_account_id for r in rows if r.dst_account_id}
    id_to_iban = {}
    if account_ids:
        accts = db.query(Account).filter(Account.id.in_(account_ids)).all()
        id_to_iban = {a.id: a.iban for a in accts}

    out: List[AlertOut] = []
    for r in rows:
        out.append(AlertOut(
<<<<<<< HEAD
            id=int(r.id), ts=r.ts,
            src_account_iban=id_to_iban.get(r.src_account_id),
            dst_account_iban=r.dst_iban or id_to_iban.get(r.dst_account_id),
            amount=float(r.amount_cents) / 100.0, currency=r.currency, channel=r.channel,
            action=r.action, reasons=list(r.risk_reasons or []),
        ))
    return out

from fastapi import HTTPException

=======
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

>>>>>>> origin/main
@app.post("/alerts/{alert_id}/decision")
def decide_alert(alert_id: int, decision: str, db: Session = Depends(get_db)):
    if decision not in {"release", "cancel"}:
        raise HTTPException(status_code=400, detail="decision must be release|cancel")
<<<<<<< HEAD

=======
    txn = db.query(Transaction).filter(Transaction.id == alert_id).one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="alert not found")
    txn.action = "allow" if decision == "release" else "hold"
    db.commit()
    return {"ok": True, "id": alert_id, "new_action": txn.action}


# ---------- Stats pentru demo ----------

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
>>>>>>> origin/main
    txn = db.query(Transaction).filter(Transaction.id == alert_id).one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="alert not found")

<<<<<<< HEAD
    # simplu: dacă release -> allow, dacă cancel -> hold
    txn.action = "allow" if decision == "release" else "hold"
    db.commit()
    return {"ok": True, "id": alert_id, "new_action": txn.action}
=======
    prev = txn.action
    score, decision, reasons = score_quiz(q)

    # Mapăm decizia de quiz pe action-ul tranzacției
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

    # pregătim maparea IBAN
    account_ids = {r.src_account_id for r in rows if r.src_account_id} | {r.dst_account_id for r in rows if r.dst_account_id}
    id_to_iban = {}
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
>>>>>>> origin/main
