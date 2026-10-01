import os
from pathlib import Path

import joblib

from app.preprocessing import preprocess


class Scorer:
    def __init__(self):
        path = Path(__file__).resolve().parents[1] / "models/model.joblib"
        artifact = joblib.load(path)
        self.model = artifact["model"]
        self.threshold = float(os.getenv("FRAUD_THRESHOLD", artifact["threshold"]))
        if not 0 <= self.threshold <= 1:
            raise ValueError("FRAUD_THRESHOLD должен быть от 0 до 1")

    def predict(self, row, transaction_id):
        score = float(self.model.predict_proba([preprocess(row)])[0, 1])
        return {"transaction_id": transaction_id, "score": score,
                "fraud_flag": int(score >= self.threshold)}
