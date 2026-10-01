import json
import os

from kafka import KafkaConsumer, KafkaProducer
from kafka.structs import OffsetAndMetadata, TopicPartition


def producer():
    return KafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
        value_serializer=lambda value: json.dumps(value, allow_nan=False).encode("utf-8"),
        acks="all", retries=10,
    )


def consumer(topic, group):
    return KafkaConsumer(
        topic, bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
        group_id=group, auto_offset_reset="earliest", enable_auto_commit=False,
        max_poll_records=1,
    )


def commit_message(client, message):

    partition = TopicPartition(message.topic, message.partition)
    client.commit({partition: OffsetAndMetadata(message.offset + 1, "", -1)})
