import argparse, json, os, sys
import pandas as pd
from sklearn.ensemble import IsolationForest
import requests
from datetime import datetime, timezone

def load_data(path):
    df = pd.read_csv(path)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df['hour'] = df['timestamp'].dt.hour
    features = ['amount','ip_risk_score','hour']
    cat_cols = ['channel','country']
    df_enc = pd.get_dummies(df[features + cat_cols], columns=cat_cols, drop_first=True)
    df_enc = df_enc.fillna(0)
    return df, df_enc

def run_iforest(X, contamination=0.08, random_state=42):
    model = IsolationForest(n_estimators=200, contamination=contamination, random_state=random_state)
    scores = model.fit_predict(X)  # -1 = outlier, 1 = normal
    return scores

def row_to_payment(row):
    ts = row.get("timestamp")
    try:
        ts = pd.to_datetime(ts, errors="coerce").to_pydatetime().astimezone(timezone.utc).isoformat()
    except Exception:
        ts = datetime.now(timezone.utc).isoformat()

    channel = str(row.get("channel", "web")).lower()
    if channel not in {"web","mobile","branch"}:
        channel = "web"

    try:
        uid = int(row.get("user_id", 0))
    except Exception:
        uid = 0

    return {
        "ts": ts,
        "src_account_iban": f"RO12BANK000000000000{uid:04d}",
        "dst_account_iban": "RO49AAAA1B31007593840000" if int(row.get("is_chargeback",0))==1 else "RO12BANK0000000000000001",
        "amount": float(row.get("amount", 0.0)),
        "currency": "RON",
        "channel": channel,
        "is_first_to_payee": True if int(row.get("is_chargeback",0))==1 else False,
        "description": None,
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="fraud-ai/data/transactions.csv")
    p.add_argument("--outdir", default="fraud-ai/output")
    p.add_argument("--contamination", type=float, default=0.08)
    p.add_argument("--alert-min-outliers", type=int, default=int(os.getenv("ALERT_MIN_OUTLIERS", "1")))
    p.add_argument("--post-to", default="", help="URL backend /scorePayment (ex: http://api:8000/scorePayment)")
    args = p.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    raw, X = load_data(args.input)
    preds = run_iforest(X, contamination=args.contamination)
    raw['anomaly'] = (preds == -1).astype(int)

    outliers = raw[raw['anomaly'] == 1].copy()
    out_csv = os.path.join(args.outdir, "outliers.csv")
    out_json = os.path.join(args.outdir, "summary.json")

    outliers.to_csv(out_csv, index=False)
    summary = {
        "input": args.input,
        "n_rows": int(len(raw)),
        "n_outliers": int(len(outliers)),
        "contamination": args.contamination,
        "alert_min_outliers": args.alert_min_outliers,
    }
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))
    print(f"[INFO] Outliers saved to: {out_csv}")

    if args.post_to:
        for _, r in outliers.iterrows():
            payload = row_to_payment(r)
            try:
                resp = requests.post(args.post_to, json=payload, timeout=5)
                print(f"[POST] {resp.status_code} -> {resp.text[:140]}")
            except requests.RequestException as e:
                print(f"[POST-ERR] {e}")

    if len(outliers) >= args.alert_min_outliers:
        sys.exit(2)

if __name__ == "__main__":
    main()
