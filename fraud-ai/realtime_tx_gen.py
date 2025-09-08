#!/usr/bin/env python3
import argparse, json, random, time, csv
from datetime import datetime, timezone
import requests
from faker import Faker

fake = Faker("ro_RO")

SAFE_IBANS = [
    "RO12BANK0000000000000001",
    "RO12BANK0000000000000002",
    "RO12BANK0000000000000003",
    "RO12BANK0000000000000004",
]
WATCHLIST_IBAN = "RO49AAAA1B31007593840000"
ALL_DST = SAFE_IBANS + [WATCHLIST_IBAN]
CHANNELS = ["web", "mobile", "branch"]

def rand_amount(risky: bool) -> float:
    return round(random.uniform(5200, 20000), 2) if risky else round(random.uniform(50, 2500), 2)

def random_iban() -> str:
    return random.choice(SAFE_IBANS)

def random_dst_iban(mule_prob: float) -> str:
    return WATCHLIST_IBAN if random.random() < mule_prob else random.choice(ALL_DST)

def maybe_payee_name(match_expected: bool) -> str:
    return "payee: John Doe Investments SRL" if match_expected else f"payee: {fake.company()}"

def gen_tx(mule_prob, risky_prob, first_to_payee_prob, cop_match_prob) -> dict:
    risky = random.random() < risky_prob
    first_to_payee = random.random() < first_to_payee_prob
    cop_match = random.random() < cop_match_prob
    src = random_iban()
    dst = random_dst_iban(mule_prob)
    amount = rand_amount(risky)
    channel = random.choice(CHANNELS)
    description = maybe_payee_name(cop_match) if random.random() < 0.9 else None
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "src_account_iban": src,
        "dst_account_iban": dst,
        "amount": amount,
        "currency": "RON",
        "channel": channel,
        "is_first_to_payee": first_to_payee,
        "description": description,
    }

def main():
    ap = argparse.ArgumentParser(description="Continuous TX generator for /scorePayment")
    ap.add_argument("--endpoint", default="http://localhost:8000/scorePayment")
    ap.add_argument("--rate", type=float, default=1.0, help="tranzactii/sec (ex: 2.0 => la 0.5s)")
    ap.add_argument("--duration", type=int, default=0, help="0 = infinit")
    ap.add_argument("--mule-prob", type=float, default=0.15)
    ap.add_argument("--risky-prob", type=float, default=0.30)
    ap.add_argument("--first-prob", type=float, default=0.50)
    ap.add_argument("--cop-match-prob", type=float, default=0.5)
    ap.add_argument("--log-csv", default="")
    args = ap.parse_args()

    period = 1.0 / max(args.rate, 0.01)
    n_sent = 0
    try:
        while True:
            n_sent += 1
            payload = gen_tx(args.mule_prob, args.risky_prob, args.first_prob, args.cop_match_prob)
            try:
                r = requests.post(args.endpoint, json=payload, timeout=5)
                if r.ok:
                    data = r.json()
                    action = data.get("action","allow")
                    print(f"[{action.upper():5}] {payload['amount']:8.2f} {payload['channel']:<6} "
                          f"dst={payload['dst_account_iban']} reasons={', '.join(data.get('reasons', []))}", flush=True)
                else:
                    print(f"[ERR  ] HTTP {r.status_code} -> {r.text[:200]}", flush=True)
            except requests.RequestException as e:
                print(f"[EXC  ] {e}", flush=True)
            if args.duration > 0 and n_sent >= int(args.rate * args.duration):
                break
            time.sleep(period)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
