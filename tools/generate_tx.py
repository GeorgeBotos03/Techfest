#!/usr/bin/env python3
import argparse, json, random, string, time, csv
from datetime import datetime, timezone
from typing import List, Tuple
import requests
from faker import Faker

fake = Faker("ro_RO")

# IBAN-uri de test (RO...) – unul este pe "watchlist" în backend
SAFE_IBANS = [
    "RO12BANK0000000000000001",
    "RO12BANK0000000000000002",
    "RO12BANK0000000000000003",
    "RO12BANK0000000000000004",
]
WATCHLIST_IBAN = "RO49AAAA1B31007593840000"  # în seed_watchlist.sql
ALL_DST = SAFE_IBANS + [WATCHLIST_IBAN]

CHANNELS = ["web", "mobile", "branch"]

def rand_amount(risky: bool) -> float:
    if risky:
        # sume mari (peste threshold 5000)
        return round(random.uniform(5200, 20000), 2)
    else:
        # sume mici/medii
        return round(random.uniform(50, 2500), 2)

def random_iban() -> str:
    return random.choice(SAFE_IBANS)

def random_dst_iban(mule_prob: float) -> str:
    return WATCHLIST_IBAN if random.random() < mule_prob else random.choice(ALL_DST)

def maybe_payee_name(match_expected: bool) -> str:
    # backend-ul așteaptă formatul "payee: <nume>" în description
    if match_expected:
        return "payee: John Doe Investments SRL"
    else:
        # un nume oarecare care să NU se potrivească
        return f"payee: {fake.company()}"

def gen_tx(
    mule_prob: float,
    risky_prob: float,
    first_to_payee_prob: float,
    cop_match_prob: float,
) -> dict:
    # decide dacă tranzacția e "risky" (sumă mare), dacă e către mule, etc.
    risky = random.random() < risky_prob
    first_to_payee = random.random() < first_to_payee_prob
    cop_match = random.random() < cop_match_prob

    src = random_iban()
    dst = random_dst_iban(mule_prob)
    amount = rand_amount(risky)
    channel = random.choice(CHANNELS)

    description = None
    # punem numele beneficiarului în descriere ca să activăm CoP simulată
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
    ap = argparse.ArgumentParser(description="Real-time TX generator for /scorePayment")
    ap.add_argument("--endpoint", default="http://localhost:8000/scorePayment", help="Scoring endpoint URL")
    ap.add_argument("--rate", type=float, default=1.0, help="tranzacții pe secundă (ex: 2.0 = la 0.5s)")
    ap.add_argument("--duration", type=int, default=60, help="durata în secunde (0 = infinit)")
    ap.add_argument("--mule-prob", type=float, default=0.1, help="probabilitate destinație mule/watchlist (0..1)")
    ap.add_argument("--risky-prob", type=float, default=0.25, help="probabilitate sumă mare (0..1)")
    ap.add_argument("--first-prob", type=float, default=0.4, help="probabilitate first-to-payee (0..1)")
    ap.add_argument("--cop-match-prob", type=float, default=0.5, help="probabilitate ca numele (CoP) să se potrivească (0..1)")
    ap.add_argument("--log-csv", default="tx_log.csv", help="fișier CSV pentru log ('' = nu loghează)")
    args = ap.parse_args()

    period = 1.0 / max(args.rate, 0.01)
    n_sent = n_ok = 0
    action_counts = {"allow": 0, "warn": 0, "hold": 0}

    csv_file = None
    writer = None
    if args.log_csv:
        csv_file = open(args.log_csv, "w", newline="", encoding="utf-8")
        writer = csv.writer(csv_file)
        writer.writerow([
            "ts","src_iban","dst_iban","amount","channel","first_to_payee","description",
            "risk_score","action","reasons","cooloff"
        ])

    print(f"Sending to {args.endpoint} | rate={args.rate}/s duration={args.duration or '∞'}s")
    t0 = time.time()
    try:
        while True:
            n_sent += 1
            payload = gen_tx(
                mule_prob=args.mule_prob,
                risky_prob=args.risky_prob,
                first_to_payee_prob=args.first_prob,
                cop_match_prob=args.cop_match_prob,
            )
            try:
                r = requests.post(args.endpoint, json=payload, timeout=5)
                if r.ok:
                    n_ok += 1
                    data = r.json()
                    action = data.get("action", "allow")
                    action_counts[action] = action_counts.get(action, 0) + 1

                    # print scurt, lizibil
                    print(f"[{action.upper():5}] {payload['amount']:8.2f} RON  "
                          f"{payload['channel']:<6}  dst={payload['dst_account_iban']}  "
                          f"reasons={', '.join(data.get('reasons', []))}")

                    # CSV
                    if writer:
                        writer.writerow([
                            payload["ts"], payload["src_account_iban"], payload["dst_account_iban"],
                            payload["amount"], payload["channel"], payload["is_first_to_payee"],
                            payload.get("description") or "",
                            data.get("risk_score", 0), action,
                            " | ".join(data.get("reasons", [])),
                            data.get("cooloff_minutes", 0),
                        ])
                else:
                    print(f"[ERR  ] HTTP {r.status_code} -> {r.text[:200]}")
            except requests.RequestException as e:
                print(f"[EXC  ] {e}")

            # timing
            if args.duration > 0 and (time.time() - t0) >= args.duration:
                break
            time.sleep(period)
    except KeyboardInterrupt:
        pass
    finally:
        if csv_file:
            csv_file.close()

    # sumar
    print("\n=== Summary ===")
    print(f"sent={n_sent} ok={n_ok}")
    for k in ["allow", "warn", "hold"]:
        print(f"{k:>5}: {action_counts.get(k,0)}")
    print("Log CSV:", args.log_csv or "<none>")

if __name__ == "__main__":
    main()
