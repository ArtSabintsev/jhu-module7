from __future__ import annotations

import logging
import time
from typing import Any

from inventory_reorder.messages import decode_sqs_body
from inventory_reorder.runtime import AppContext
from inventory_reorder.settings import Settings

logger = logging.getLogger(__name__)


def process_alert_event(event: dict[str, Any], context: AppContext) -> dict[str, Any]:
    if event.get("event_type") not in (None, "reorder.alert.opened"):
        raise ValueError(f"Unexpected alert event_type: {event.get('event_type')}")
    if event.get("schema_version") not in (None, 1):
        raise ValueError(f"Unsupported alert schema_version: {event.get('schema_version')}")

    alert = event.get("payload", event)
    notification = context.storage.record_notification(alert)
    context.storage.mark_alert_notified(alert["alert_id"])
    logger.info(
        "recorded manager notification sku=%s alert_id=%s notification_id=%s",
        alert["sku"],
        alert["alert_id"],
        notification["notification_id"],
    )
    return notification


def run_forever(context: AppContext) -> None:
    settings = context.settings
    if settings.is_vultr:
        settings.require("kafka_alert_topic", "kafka_alert_group")
        context.kafka.consume_forever(
            settings.kafka_alert_topic,
            settings.kafka_alert_group,
            lambda event: process_alert_event(event, context),
        )
        return

    settings.require("alert_queue_url")
    logger.info("alert notifier polling queue=%s", settings.alert_queue_url)

    while True:
        response = context.aws.sqs.receive_message(
            QueueUrl=settings.alert_queue_url,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=settings.poll_wait_seconds,
        )
        for message in response.get("Messages", []):
            receipt_handle = message["ReceiptHandle"]
            try:
                event = decode_sqs_body(message["Body"])
                process_alert_event(event, context)
                context.aws.sqs.delete_message(
                    QueueUrl=settings.alert_queue_url,
                    ReceiptHandle=receipt_handle,
                )
            except Exception:
                logger.exception("failed to process alert message")
        time.sleep(0.2)


def main() -> None:
    settings = Settings.from_env()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    run_forever(AppContext(settings))


if __name__ == "__main__":
    main()
