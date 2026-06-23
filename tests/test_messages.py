import json
from types import SimpleNamespace

from inventory_reorder.messages import decode_sqs_body, inventory_event
from inventory_reorder.models import InventoryUpdate
from inventory_reorder.vultr_messaging import decode_consumer_record


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


def test_decode_kafka_consumer_record_value_attribute() -> None:
    message = SimpleNamespace(
        value=json.dumps({"event_type": "inventory.updated"}).encode("utf-8")
    )

    assert decode_consumer_record(message)["event_type"] == "inventory.updated"


def test_decode_kafka_consumer_record_value_callable() -> None:
    payload = json.dumps({"event_type": "reorder.alert.opened"}).encode("utf-8")
    message = SimpleNamespace(value=lambda: payload)

    assert decode_consumer_record(message)["event_type"] == "reorder.alert.opened"
