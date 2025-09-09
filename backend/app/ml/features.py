# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Dict, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

NUMERIC = ["amount", "is_first_to_payee"]
CATEGORICAL = ["channel"]
TEXT = "description"

CHANNELS = ["web", "mobile", "branch"]

def prepare_xy(rows: List[Dict], labels: List[int], vectorizer: TfidfVectorizer | None = None
              ) -> Tuple[np.ndarray, np.ndarray, TfidfVectorizer]:
    """
    Transformă listă de tranzacții în X (features) + y (labels).
    - Numeric: amount, is_first_to_payee
    - Categorical: channel (one-hot)
    - Text: description (TF-IDF)
    Returnează (X, y, vectorizer) unde X = [num | onehot | tfidf]
    """
    import numpy as np

    # numeric
    num = np.array([[float(r.get("amount", 0.0)),
                     1.0 if r.get("is_first_to_payee") else 0.0] for r in rows], dtype=np.float32)

    # categorical one-hot (channel)
    ch_idx = {c:i for i, c in enumerate(CHANNELS)}
    onehot = np.zeros((len(rows), len(CHANNELS)), dtype=np.float32)
    for i, r in enumerate(rows):
        c = r.get("channel", "web")
        j = ch_idx.get(c, 0)
        onehot[i, j] = 1.0

    # text
    texts = [(r.get("description") or "").lower() for r in rows]
    if vectorizer is None:
        vectorizer = TfidfVectorizer(min_df=2, max_df=0.9, ngram_range=(1,2))
        tf = vectorizer.fit_transform(texts)
    else:
        tf = vectorizer.transform(texts)

    # spars -> dens pentru concat simplu (date mici)
    tf_dense = tf.toarray().astype(np.float32)

    X = np.concatenate([num, onehot, tf_dense], axis=1)
    y = np.array(labels, dtype=np.int32)
    return X, y, vectorizer
