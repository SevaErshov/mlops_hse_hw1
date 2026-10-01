import json
import zipfile
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

from app.preprocessing import preprocess


def main():
    root = Path(__file__).resolve().parents[1]
    with zipfile.ZipFile(root / "teta-ml-1-2025.zip") as archive:
        with archive.open("train.csv") as source:
            data = pd.read_csv(source)
        with archive.open("test.csv") as source:
            demo = pd.read_csv(source, nrows=500)
    demo.to_csv(root / "data/demo.csv", index=False)

    if len(data) > 120000:
        data, _ = train_test_split(data, train_size=120000, stratify=data.target, random_state=42)
    train, rest = train_test_split(data, test_size=0.3, stratify=data.target, random_state=42)
    validation, test = train_test_split(rest, test_size=0.5, stratify=rest.target, random_state=42)
    features = lambda frame: [preprocess(row) for row in frame.to_dict("records")]
    model = make_pipeline(DictVectorizer(), RandomForestClassifier(
        n_estimators=60, max_depth=12, min_samples_leaf=2,
        class_weight="balanced_subsample", random_state=42, n_jobs=2,
    ))
    model.fit(features(train), train.target)
    probabilities = model.predict_proba(features(validation))[:, 1]
    thresholds = np.arange(0.05, 0.96, 0.025)
    threshold = round(float(max(thresholds, key=lambda t: f1_score(validation.target, probabilities >= t))), 3)
    probabilities = model.predict_proba(features(test))[:, 1]
    predictions = probabilities >= threshold
    metrics = {
        "model": "DictVectorizer + RandomForestClassifier (60 trees, depth 12)",
        "train_rows": len(train), "validation_rows": len(validation), "test_rows": len(test),
        "fraud_rate": float(data.target.mean()), "seed": 42,
        "threshold": threshold,
        "f1": f1_score(test.target, predictions),
        "precision": precision_score(test.target, predictions, zero_division=0),
        "recall": recall_score(test.target, predictions),
        "roc_auc": roc_auc_score(test.target, probabilities),
        "average_precision": average_precision_score(test.target, probabilities),
        "split": "stratified random 70/15/15; threshold selected on validation only",
    }
    joblib.dump({"model": model, "threshold": threshold}, root / "models/model.joblib", compress=3)
    (root / "models/metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
