import json
import logging

from app.kafka_utils import commit_message, consumer, producer
from app.scorer import Scorer


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    model = Scorer()
    client = consumer("transactions", "fraud-scorer-v1")
    output = producer()
    try:
        for message in client:
            try:
                row = json.loads(message.value)
                if not isinstance(row, dict):
                    raise ValueError("Ожидается JSON-объект")
                transaction_id = str(row.get("transaction_id") or f"{message.topic}-{message.partition}-{message.offset}")
                result = model.predict(row, transaction_id)
            except (ValueError, KeyError, TypeError, OverflowError) as error:

                output.send("errors", {"topic": message.topic, "partition": message.partition,
                                       "offset": message.offset, "error": str(error)}).get(timeout=30)
                commit_message(client, message)
                logging.warning("Пропущена некорректная транзакция: %s", error)
                continue
            output.send("scores", result).get(timeout=30)
            commit_message(client, message)
            logging.info("Транзакция %s, score=%.4f", transaction_id, result["score"])
    finally:
        output.close()
        client.close()


if __name__ == "__main__":
    main()
