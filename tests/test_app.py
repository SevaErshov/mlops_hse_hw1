import csv
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
from streamlit.testing.v1 import AppTest

from app.preprocessing import preprocess
from app.scorer import Scorer
from app.writer import validate_score
from app.kafka_utils import commit_message


class ScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open("data/demo.csv") as source:
            cls.rows = list(csv.DictReader(source))
        cls.scorer = Scorer()

    def test_real_test_csv(self):
        scores = []
        for row in self.rows:
            result = self.scorer.predict(row, "test")
            validate_score(result)
            self.assertEqual(result["fraud_flag"], int(result["score"] >= self.scorer.threshold))
            scores.append(result["score"])
        self.assertGreater(len(set(scores)), 1)

    def test_no_target_leak(self):
        row = self.rows[0]
        self.assertEqual(preprocess(row), preprocess({**row, "target": 1, "transaction_id": "abc"}))

    def test_invalid_number(self):
        for value in ("NaN", "inf", "-1"):
            with self.assertRaises(ValueError):
                preprocess({**self.rows[0], "amount": value})

    def test_unknown_category(self):
        result = self.scorer.predict({**self.rows[0], "cat_id": "new_category"}, "new")
        validate_score(result)

    def test_invalid_score_message(self):
        for value in (float("nan"), 2, -1, "0.5"):
            with self.assertRaises(ValueError):
                validate_score({"transaction_id": "a", "score": value, "fraud_flag": 0})

    def test_model_affects_score(self):
        with patch.object(self.scorer.model, "predict_proba", return_value=np.array([[0.01, 0.99]])):
            result = self.scorer.predict(self.rows[0], "a")
        self.assertEqual(result["score"], 0.99)
        self.assertEqual(result["fraud_flag"], 1)

    def test_commit_only_processed_offset(self):
        client = Mock()
        commit_message(client, SimpleNamespace(topic="transactions", partition=0, offset=12))
        offsets = client.commit.call_args.args[0]
        self.assertEqual(len(offsets), 1)
        self.assertEqual(next(iter(offsets.values())).offset, 13)


class InterfaceTests(unittest.TestCase):
    def test_empty_database(self):
        with patch("app.database.read_results", return_value=([], [])):
            ui = AppTest.from_file("app/ui.py").run()
            ui.button[1].click().run()
            self.assertEqual(len(ui.exception), 0)
            self.assertEqual(len(ui.info), 2)

    def test_results(self):
        with patch("app.database.read_results", return_value=([("abc", 0.9, 1, "2026-01-01")], [0.1, 0.9])):
            ui = AppTest.from_file("app/ui.py").run()
            ui.button[1].click().run()
            self.assertEqual(len(ui.exception), 0)
            self.assertEqual(len(ui.dataframe), 1)
            self.assertEqual(len(ui.get("arrow_vega_lite_chart")), 1)


if __name__ == "__main__":
    unittest.main()
