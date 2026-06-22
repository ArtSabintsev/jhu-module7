from __future__ import annotations

import logging
import time
from typing import Any

from inventory_reorder.decision import evaluate_reorder
from inventory_reorder.messages import alert_event, decode_sqs_body, publish_json
from inventory_reorder.models import InventoryUpdate
from inventory_reorder.runtime import AppContext
from inventory_reorder.settings import Settings

logger = logging.getLogger(__name__)


def process_inventory_event(event: dict[str, Any], context: AppContext) -> str:
    payload = event.get("payload", event)
    update = InventoryUpdate.model_validate(payload)
    decision = evaluate_reorder(update)

    record = context.storage.put_inventory(update, decision.status)
    context.cache.set_json(f"inventory:{update.sku}", record)
    context.cache.delete("inventory:all")

    if decision.reorder_needed:
        context.settings.require("alert_topic_arn")
        alert = context.storage.upsert_open_alert(update, decision.reason)
        context.cache.delete("alerts:open")
        message_id = publish_json(
            context.aws.sns,
            context.settings.alert_topic_arn,
            f"Reorder needed {update.sku}",
            alert_event(alert),
        )
        logger.info(
            "created reorder alert sku=%s alert_id=%s sns_message_id=%s",
            update.sku,
            alert["alert_id"],
            message_id,
        )
        return "ALERT_OPENED"

    resolved_count = context.storage.resolve_open_alerts(update.sku)
    if resolved_count:
        context.cache.delete("alerts:open")
    logger.info("inventory healthy sku=%s resolved_alerts=%s", update.sku, resolved_count)
    return "HEALTHY"


def run_forever(context: AppContext) -> None:
    settings = context.settings
    settings.require("inventory_queue_url")
    logger.info("inventory worker polling queue=%s", settings.inventory_queue_url)

    while True:
        response = context.aws.sqs.receive_message(
            QueueUrl=settings.inventory_queue_url,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=settings.poll_wait_seconds,
        )
        for message in response.get("Messages", []):
            receipt_handle = message["ReceiptHandle"]
            try:
                event = decode_sqs_body(message["Body"])
                result = process_inventory_event(event, context)
                context.aws.sqs.delete_message(
                    QueueUrl=settings.inventory_queue_url,
                    ReceiptHandle=receipt_handle,
                )
                logger.info("processed inventory message result=%s", result)
            except Exception:
                logger.exception("failed to process inventory message")
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
