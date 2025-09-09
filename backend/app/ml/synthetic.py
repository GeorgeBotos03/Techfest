# -*- coding: utf-8 -*-
from __future__ import annotations
import random, datetime as dt
from typing import List, Dict, Tuple

CHANNELS = ["web", "mobile", "branch"]

INVEST_TEMPLATES = [
    "urgent transfer to crypto exchange investment opportunity",
    "invest in bitcoin fast profit",
    "broker said quick return investment",
    "crypto exchange top up",
]
ROMANCE_TEMPLATES = [
    "love gift support for partner",
    "urgent money to my fiancee abroad",
    "help my girlfriend with loan refund",
]
TAX_TEMPLATES = [
    "tax refund processing fee",
    "urgent transfer for tax clearance",
    "payment for tax office finalization",
]
IMPERSONATION_TEMPLATES = [
    "bank security safe account transfer",
    "police requested urgent transfer",
    "IT support remote access fee",
]

LEGIT_TEMPLATES = [
    "payee: Acme SRL invoice 1021",
    "payee: Endava SRL services",
    "rent payment",
    "utilities bill",
    "school fee",
]

SCAM_TYPES = {
    "investment": INVEST_TEMPLATES,
    "romance": ROMANCE_TEMPLATES,
    "tax_refund": TAX_TEMPLATES,
    "impersonation": IMPERSONATION_TEMPLATES,
}

def _rand_iban(prefix="RO", bank="BANK", acc_len=16) -> str:
    return f"{prefix}12{bank}{random.randint(10**(acc_len-1), 10**acc_len-1)}"

def _rand_ts() -> str:
    now = dt.datetime.utcnow()
    skew = dt.timedelta(minutes=random.randint(-60*24, 0))
    return (now + skew).replace(microsecond=0).isoformat() + "Z"

def _pick_channel() -> str:
    return random.choices(CHANNELS, weights=[0.45, 0.45, 0.10])[0]

def generate_samples(n: int = 2000, scam_ratio: float = 0.5, seed: int | None = 42
                   ) -> Tuple[List[Dict], List[int], List[str]]:
    """
    Returnează (samples, labels, tags) unde:
      samples: list payload-uri asemănătoare PaymentIn
      labels: 1=scam, 0=legit
      tags: eticheta de scenariu ("investment", "romance", etc. sau "legit")
    """
    if seed is not None:
        random.seed(seed)

    samples: List[Dict] = []
    labels: List[int] = []
    tags: List[str] = []

    num_scam = int(n * scam_ratio)
    num_leg  = n - num_scam

    # Scam
    scam_types = list(SCAM_TYPES.keys())
    for _ in range(num_scam):
        t = random.choice(scam_types)
        desc = random.choice(SCAM_TYPES[t])
        amount = random.choice([3500, 5200, 9000, 15000, 25000])
        payload = {
            "ts": _rand_ts(),
            "src_account_iban": _rand_iban(bank="SRC"),
            "dst_account_iban": _rand_iban(bank="DST"),
            "amount": float(amount),
            "currency": "RON",
            "channel": _pick_channel(),
            "is_first_to_payee": True,
            "description": desc
        }
        samples.append(payload)
        labels.append(1)
        tags.append(t)

    # Legit
    for _ in range(num_leg):
        desc = random.choice(LEGIT_TEMPLATES)
        amount = random.choice([50, 100, 250, 800, 1200, 3000])
        payload = {
            "ts": _rand_ts(),
            "src_account_iban": _rand_iban(bank="SRC"),
            "dst_account_iban": _rand_iban(bank="DST"),
            "amount": float(amount),
            "currency": "RON",
            "channel": _pick_channel(),
            "is_first_to_payee": random.random() < 0.2,
            "description": desc
        }
        samples.append(payload)
        labels.append(0)
        tags.append("legit")

    # mic shuffle
    idx = list(range(n))
    random.shuffle(idx)
    samples = [samples[i] for i in idx]
    labels  = [labels[i]  for i in idx]
    tags    = [tags[i]    for i in idx]
    return samples, labels, tags
