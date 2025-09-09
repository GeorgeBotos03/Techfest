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
    channel: str                       # web|mobile|branch
    is_first_to_payee: bool = False
    device_fp: Optional[str] = None
    description: Optional[str] = None  # ex: "payee: ACME SRL"

class ScoreOut(BaseModel):
    risk_score: float
    action: str                        # allow|warn|hold
    reasons: List[str] = []
    cooloff_minutes: int = 0

class AlertOut(BaseModel):
    id: int
    ts: datetime
<<<<<<< HEAD
    src_account_iban: Optional[str] = None
    dst_account_iban: Optional[str] = None
=======
    src_account_iban: str | None = None
    dst_account_iban: str | None = None
>>>>>>> origin/main
    amount: float
    currency: str
    channel: str
    action: str
<<<<<<< HEAD
    reasons: List[str] = []
=======
    reasons: list[str] = []

class QuizIn(BaseModel):
    was_called_by_someone_claiming_bank: bool = False
    was_asked_to_invest_or_crypto: bool = False
    screen_sharing_or_remote_access: bool = False
    verified_beneficiary_yourself: bool = True
    notes: str | None = None

class QuizOut(BaseModel):
    id: int
    previous_action: str
    new_action: str
    score: int
    reasons: list[str]
>>>>>>> origin/main
