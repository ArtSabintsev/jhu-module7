from __future__ import annotations

import json
from typing import Any

from inventory_reorder.models import InventoryUpdate, JsonDict


def inventory_event(update: InventoryUpdate) -> JsonDict:
    return {
        "event_type": "inventory.updated",
        "schema_version": 1,
        "payload": update.model_dump(mode="json"),
    }


def alert_event(alert: JsonDict) -> JsonDict:
    return {
        "event_type": "reorder.alert.opened",
        "schema_version": 1,
        "payload": alert,
    }


def publish_json(sns_client: Any, topic_arn: str, subject: str, payload: JsonDict) -> str:
    response = sns_client.publish(
        TopicArn=topic_arn,
        Subject=subject[:100],
        Message=json.dumps(payload, separators=(",", ":"), sort_keys=True),
        MessageAttributes={
            "event_type": {
                "DataType": "String",
                "StringValue": str(payload.get("event_type", "unknown")),
            }
        },
    )
    return response["MessageId"]


def decode_sqs_body(body: str) -> JsonDict:
    decoded = json.loads(body)
    message = decoded.get("Message")
    if isinstance(message, str):
        return json.loads(message)
    return decoded
