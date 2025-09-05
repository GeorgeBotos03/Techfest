import argparse, json, os, sys
import pandas as pd
from sklearn.ensemble import IsolationForest

def load_data(path):
    df = pd.read_csv(path)
    # feature engineering minimal
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df['hour'] = df['timestamp'].dt.hour
    features = ['amount','ip_risk_score','hour']
    cat_cols = ['channel','country']
    df_enc = pd.get_dummies(df[features + cat_cols], columns=cat_cols, drop_first=True)
    df_enc = df_enc.fillna(0)
    return df, df_enc

def run_iforest(X, contamination=0.08, random_state=42):
    model = IsolationForest(n_estimators=200, contamination=contamination, random_state=random_state)
    scores = model.fit_predict(X)          # -1 = outlier, 1 = normal
    return scores

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="fraud-ai/data/transactions.csv")
    p.add_argument("--outdir", default="fraud-ai/output")
    p.add_argument("--contamination", type=float, default=0.08)
    p.add_argument("--alert-min-outliers", type=int, default=int(os.getenv("ALERT_MIN_OUTLIERS", "1")))
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
    if len(outliers) >= args.alert_min_outliers:
        # non-zero ca să poți FAIL-ui pipeline-ul dacă vrei
        sys.exit(2)

if __name__ == "__main__":
    main()
