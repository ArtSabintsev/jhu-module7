from __future__ import annotations

import json
import logging
from typing import Any, Callable
from uuid import uuid4

from kafka.admin import KafkaAdminClient, NewTopic
from kafka import KafkaConsumer, KafkaProducer

from inventory_reorder.models import JsonDict
from inventory_reorder.settings import Settings

logger = logging.getLogger(__name__)


def _base_kafka_config(settings: Settings) -> dict[str, Any]:
    settings.require("kafka_bootstrap_servers")
    config = {
        "bootstrap_servers": settings.kafka_bootstrap_servers.split(","),
        "security_protocol": settings.kafka_security_protocol,
    }
    if settings.kafka_security_protocol.upper() != "PLAINTEXT":
        settings.require("kafka_username", "kafka_password")
        config.update(
            {
                "sasl_mechanism": settings.kafka_sasl_mechanism,
                "sasl_plain_username": settings.kafka_username,
                "sasl_plain_password": settings.kafka_password,
            }
        )
    return config


class KafkaEventBus:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.producer = KafkaProducer(**_base_kafka_config(settings))

    def publish(self, topic: str, subject: str, payload: JsonDict) -> str:
        message_id = str(uuid4())
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        key = _message_key(payload)
        self.producer.send(
            topic,
            key=key.encode("utf-8") if key else None,
            value=body.encode("utf-8"),
            headers=[
                ("message_id", message_id.encode("utf-8")),
                ("subject", subject[:100].encode("utf-8")),
                ("event_type", str(payload.get("event_type", "unknown")).encode("utf-8")),
            ],
        )
        self.producer.flush(10)
        return message_id

    def consume_forever(
        self,
        topic: str,
        group_id: str,
        handler: Callable[[JsonDict], None],
    ) -> None:
        consumer = KafkaConsumer(
            topic,
            **_base_kafka_config(self.settings),
            group_id=group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        )
        logger.info("kafka consumer subscribed topic=%s group_id=%s", topic, group_id)

        try:
            for message in consumer:
                event = json.loads(message.value().decode("utf-8"))
                handler(event)
                consumer.commit()
        finally:
            consumer.close()


def _message_key(payload: JsonDict) -> str | None:
    inner = payload.get("payload")
    if isinstance(inner, dict) and inner.get("sku"):
        return str(inner["sku"])
    return None


def initialize_topics(settings: Settings) -> list[str]:
    admin = KafkaAdminClient(
        client_id="jhu-module7-topic-init",
        **_base_kafka_config(settings),
    )
    topics = [settings.kafka_inventory_topic, settings.kafka_alert_topic]
    existing = set(admin.list_topics())
    missing = [
        NewTopic(
            name=topic,
            num_partitions=settings.kafka_topic_partitions,
            replication_factor=settings.kafka_topic_replication_factor,
        )
        for topic in topics
        if topic not in existing
    ]
    if missing:
        admin.create_topics(missing)
    admin.close()
    return [topic.name for topic in missing]


def main() -> None:
    settings = Settings.from_env()
    created = initialize_topics(settings)
    if created:
        print("Created Kafka topics: " + ", ".join(created))
    else:
        print("Kafka topics already exist.")
