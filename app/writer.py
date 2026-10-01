import json
import logging
import math

from app.database import connect, save_score
from app.kafka_utils import commit_message, consumer, producer


def validate_score(row):
    if not isinstance(row, dict) or set(row) != {"transaction_id", "score", "fraud_flag"}:
        raise ValueError("Ожидаются transaction_id, score, fraud_flag")
    if not isinstance(row["transaction_id"], str) or not row["transaction_id"]:
        raise ValueError("Пустой transaction_id")
    if type(row["score"]) not in (int, float) or not math.isfinite(row["score"]) or not 0 <= row["score"] <= 1:
        raise ValueError("Некорректный score")
    if type(row["fraud_flag"]) is not int or row["fraud_flag"] not in (0, 1):
        raise ValueError("Некорректный fraud_flag")


def main():
    logging.basicConfig(level=logging.INFO)
    client = consumer("scores", "postgres-writer-v1")
    output = producer()
    connection = connect()
    try:
        for message in client:
            try:
                row = json.loads(message.value)
                validate_score(row)
            except (ValueError, TypeError) as error:
                output.send("errors", {"topic": message.topic, "partition": message.partition,
                                       "offset": message.offset, "error": str(error)}).get(timeout=30)
                commit_message(client, message)
                continue
            save_score(connection, row)

            commit_message(client, message)
            logging.info("Записана транзакция %s", row["transaction_id"])
    finally:
        connection.close()
        output.close()
        client.close()


if __name__ == "__main__":
    main()
