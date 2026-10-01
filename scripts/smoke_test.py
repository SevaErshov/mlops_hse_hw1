import csv
import json
import time
from uuid import uuid4

from app.database import connect
from app.kafka_utils import consumer, producer
from app.scorer import Scorer


def main():
    with open("data/demo.csv") as source:
        rows = list(csv.DictReader(source))[:10]
    expected = {}
    model = Scorer()
    output = producer()
    for row in rows:
        row["transaction_id"] = "smoke-" + str(uuid4())
        expected[row["transaction_id"]] = model.predict(row, row["transaction_id"])
        output.send("transactions", row).get(timeout=30)

    output.send("transactions", rows[0]).get(timeout=30)
    output.close()
    client = consumer("scores", "smoke-" + str(uuid4()))
    seen = set()
    deadline = time.monotonic() + 90
    connection = connect()
    try:
        while time.monotonic() < deadline:
            for batch in client.poll(timeout_ms=500).values():
                for message in batch:
                    result = json.loads(message.value)
                    key = result.get("transaction_id")
                    if key in expected:
                        assert set(result) == {"transaction_id", "score", "fraud_flag"}
                        assert abs(result["score"] - expected[key]["score"]) < 1e-10
                        assert result["fraud_flag"] == expected[key]["fraud_flag"]
                        seen.add(key)
            with connection.cursor() as cursor:
                cursor.execute("SELECT transaction_id, score, fraud_flag FROM transaction_scores WHERE transaction_id = ANY(%s)", (list(expected),))
                saved = cursor.fetchall()
            connection.commit()
            if seen == set(expected) and len(saved) == len(expected):
                for key, score, flag in saved:
                    assert abs(score - expected[key]["score"]) < 1e-10
                    assert flag == expected[key]["fraud_flag"]
                print("OK: 10 транзакций прошли Kafka → модель → scores → PostgreSQL")
                return
        raise RuntimeError(f"Таймаут: scores={len(seen)}, PostgreSQL={len(saved)}")
    finally:
        client.close()
        connection.close()


if __name__ == "__main__":
    main()
