# -*- coding: utf-8 -*-
from __future__ import annotations
import os, json
from dataclasses import dataclass
from typing import List, Dict, Tuple
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle

from app.ml.synthetic import generate_samples
from app.ml.features import prepare_xy

ART_DIR = os.getenv("ML_ART_DIR", "/app/app/ml/artifacts")
MODEL_PATH = os.path.join(ART_DIR, "model.pkl")
VECT_PATH  = os.path.join(ART_DIR, "vectorizer.pkl")
META_PATH  = os.path.join(ART_DIR, "meta.json")

os.makedirs(ART_DIR, exist_ok=True)

@dataclass
class MLState:
    clf: LogisticRegression | None = None
    vect: any = None
    meta: Dict = None

ml_state = MLState(clf=None, vect=None, meta={})

def train_and_save(n: int = 3000, scam_ratio: float = 0.5, seed: int = 42) -> Dict:
    rows, labels, tags = generate_samples(n=n, scam_ratio=scam_ratio, seed=seed)
    X, y, vect = prepare_xy(rows, labels, vectorizer=None)

    X, y = shuffle(X, y, random_state=seed)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=seed, stratify=y)

    clf = LogisticRegression(max_iter=200, n_jobs=1)
    clf.fit(Xtr, ytr)

    proba = clf.predict_proba(Xte)[:,1]
    auc = float(roc_auc_score(yte, proba))
    acc = float(accuracy_score(yte, (proba>=0.5).astype(int)))

    # persist
    joblib.dump(clf, MODEL_PATH)
    joblib.dump(vect, VECT_PATH)
    meta = {"n": n, "scam_ratio": scam_ratio, "seed": seed, "auc": auc, "acc": acc}
    with open(META_PATH, "w") as f:
        json.dump(meta, f)

    # cache in memorie
    ml_state.clf = clf
    ml_state.vect = vect
    ml_state.meta = meta
    return meta

def try_load() -> bool:
    if not (os.path.exists(MODEL_PATH) and os.path.exists(VECT_PATH)):
        return False
    try:
        ml_state.clf = joblib.load(MODEL_PATH)
        ml_state.vect = joblib.load(VECT_PATH)
        if os.path.exists(META_PATH):
            import json
            with open(META_PATH) as f:
                ml_state.meta = json.load(f)
        else:
            ml_state.meta = {}
        return True
    except Exception:
        return False

def predict_proba_one(row: Dict) -> float | None:
    if ml_state.clf is None or ml_state.vect is None:
        return None
    X, _, _ = prepare_xy([row], [0], vectorizer=ml_state.vect)
    proba = float(ml_state.clf.predict_proba(X)[:,1][0])
    return proba

def status() -> Dict:
    loaded = ml_state.clf is not None
    info = {"loaded": loaded}
    if loaded:
        info["meta"] = ml_state.meta or {}
    return info
