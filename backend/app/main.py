from fastapi import FastAPI, Depends
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import select
from app.schemas import AlertOut
from app.models import Account, Transaction, Customer  # deja ai astea importate
from fastapi import HTTPException


from app.schemas import PaymentIn, ScoreOut
from app.services.scoring import score_payment
from app.services.cop_check import confirmation_of_payee
from app.services.mule_graph import update_graph, mule_risk
from app.deps import get_db
from app.models import Account, Transaction, Customer

app = FastAPI(title="Anti-Scam API")


@app.get("/")
def root():
    """Mic index pentru a evita pagina goală când deschizi rădăcina /"""
    return {"status": "ok", "health": "/health", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}


@app.post("/scorePayment", response_model=ScoreOut)
async def score_payment_endpoint(p: PaymentIn, db: Session = Depends(get_db)):
    # Deducem numele beneficiarului (CoP simulată) din description: "payee: <nume>"
    provided_name = None
    if p.description and "payee:" in p.description.lower():
        provided_name = p.description.split(":", 1)[1].strip()

    # Confirmation of Payee (simulat)
    cop_ok, cop_msg = await confirmation_of_payee(p.dst_account_iban, provided_name)

    # Actualizează graful "Mule Radar" și obține un risc simplu pentru IBAN destinație
    update_graph(p.src_account_iban, p.dst_account_iban, p.amount)
    mule_r = mule_risk(p.dst_account_iban)
    on_watchlist = mule_r >= 80

    # Feature-uri de scorare
    features = {
        "amount": p.amount,
        "channel": p.channel,
        "is_first_to_payee": p.is_first_to_payee,
    }

    # Scorare pe reguli
    score, action, reasons, cooloff = await score_payment(features, cop_ok, on_watchlist)

    if not cop_ok:
        reasons.append(f"CoP: {cop_msg}")
    if mule_r >= 60:
        reasons.append(f"MuleRadar risk={mule_r}")
    if on_watchlist:
        reasons.append("Beneficiary on watchlist")

    # === Persistență minimă în Postgres ===
    # 1) Asigură contul sursă
    src_acct = db.query(Account).filter(Account.iban == p.src_account_iban).one_or_none()
    if not src_acct:
        # Creează un client demo dacă lipsește
        cust = db.query(Customer).filter(Customer.external_id == "demo").one_or_none()
        if not cust:
            cust = Customer(external_id="demo", name="Demo User")
            db.add(cust)
            db.flush()
        src_acct = Account(customer_id=cust.id, iban=p.src_account_iban)
        db.add(src_acct)
        db.flush()

    # 2) (Opțional) cont destinație dacă e intern
    dst_acct = db.query(Account).filter(Account.iban == p.dst_account_iban).one_or_none()
    dst_account_id = dst_acct.id if dst_acct else None

    # 3) Inserează tranzacția scorată
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

@app.get("/alerts", response_model=List[AlertOut])
def list_alerts(db: Session = Depends(get_db)):
    # tranzacții cu acțiune != allow, cele mai noi primele
    q = select(Transaction).where(Transaction.action != "allow").order_by(Transaction.id.desc()).limit(200)
    rows = db.execute(q).scalars().all()

    # mapare id->iban pentru conturi (doar dacă există)
    account_ids = {r.src_account_id for r in rows if r.src_account_id} | {r.dst_account_id for r in rows if r.dst_account_id}
    id_to_iban = {}
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
    # simplu: marcăm action în funcție de decizie
    txn.action = "allow" if decision == "release" else "hold"
    db.commit()
    return {"ok": True, "id": alert_id, "new_action": txn.action}