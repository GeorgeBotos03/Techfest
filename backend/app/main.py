from fastapi import FastAPI
from datetime import datetime
from app.schemas import PaymentIn, ScoreOut
from app.services.scoring import score_payment
from app.services.cop_check import confirmation_of_payee
from app.services.mule_graph import update_graph, mule_risk

app = FastAPI(title="Anti-Scam API")

@app.get("/")
def root():
    return {"status": "ok", "health": "/health", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}

@app.post("/scorePayment", response_model=ScoreOut)
async def score_payment_endpoint(p: PaymentIn):
    provided_name = None
    if p.description and "payee:" in p.description.lower():
        provided_name = p.description.split(":", 1)[1].strip()

    cop_ok, cop_msg = await confirmation_of_payee(p.dst_account_iban, provided_name)

    update_graph(p.src_account_iban, p.dst_account_iban, p.amount)
    mule_r = mule_risk(p.dst_account_iban)
    on_watchlist = mule_r >= 80

    features = {
        "amount": p.amount,
        "channel": p.channel,
        "is_first_to_payee": p.is_first_to_payee,
    }

    score, action, reasons, cooloff = await score_payment(features, cop_ok, on_watchlist)

    if not cop_ok:
        reasons.append(f"CoP: {cop_msg}")
    if mule_r >= 60:
        reasons.append(f"MuleRadar risk={mule_r}")

    return ScoreOut(risk_score=score, action=action, reasons=reasons, cooloff_minutes=cooloff)
