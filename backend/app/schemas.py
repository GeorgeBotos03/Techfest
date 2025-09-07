from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from typing import Any

class PaymentIn(BaseModel):
    ts: datetime
    src_account_iban: str
    dst_account_iban: str
    amount: float
    currency: str = Field(min_length=3, max_length=3)
    channel: str  # web|mobile|branch
    is_first_to_payee: bool = False
    device_fp: Optional[str] = None
    description: Optional[str] = None  # for Reason Check

class ScoreOut(BaseModel):
    risk_score: float
    action: str  # allow|warn|hold
    reasons: List[str] = []
    cooloff_minutes: int = 0

class AlertOut(BaseModel):
    id: int
    ts: datetime
    src_account_iban: str | None = None
    dst_account_iban: str | None = None
    amount: float
    currency: str
    channel: str
    action: str
    reasons: list[str] = []
