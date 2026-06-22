import json

from inventory_reorder.messages import decode_sqs_body, inventory_event
from inventory_reorder.models import InventoryUpdate


def test_inventory_event_has_expected_shape() -> None:
    update = InventoryUpdate(
        sku="LOLLY-001",
        name="Cherry Lollipop",
        quantity=5,
        reorder_threshold=12,
    )

    event = inventory_event(update)

    assert event["event_type"] == "inventory.updated"
    assert event["schema_version"] == 1
    assert event["payload"]["sku"] == "LOLLY-001"


def test_decode_plain_sqs_body() -> None:
    body = json.dumps({"event_type": "inventory.updated", "payload": {"sku": "A"}})

    assert decode_sqs_body(body)["event_type"] == "inventory.updated"


def test_decode_sns_wrapped_sqs_body() -> None:
    inner = {"event_type": "reorder.alert.opened", "payload": {"sku": "A"}}
    body = json.dumps({"Type": "Notification", "Message": json.dumps(inner)})

    assert decode_sqs_body(body) == inner
