from types import SimpleNamespace

from inventory_reorder.notifier import process_alert_event
from inventory_reorder.worker import process_inventory_event


class FakeSettings:
    is_vultr = False
    alert_topic_arn = "arn:aws:sns:us-east-1:123456789012:test-alerts"

    def require(self, *names: str) -> None:
        for name in names:
            assert getattr(self, name)


class FakeSns:
    def __init__(self) -> None:
        self.published: list[dict[str, object]] = []

    def publish(self, **kwargs: object) -> dict[str, str]:
        self.published.append(kwargs)
        return {"MessageId": "message-123"}


class FakeCache:
    def __init__(self) -> None:
        self.values: dict[str, object] = {}
        self.deleted: list[str] = []

    def set_json(self, key: str, value: object) -> None:
        self.values[key] = value

    def delete(self, *keys: str) -> None:
        self.deleted.extend(keys)


class FakeStorage:
    def __init__(self) -> None:
        self.inventory: list[dict[str, object]] = []
        self.alerts: list[dict[str, object]] = []
        self.notifications: list[dict[str, object]] = []
        self.notified_alerts: list[str] = []

    def put_inventory(self, update, status: str) -> dict[str, object]:
        item = {"sku": update.sku, "status": status}
        self.inventory.append(item)
        return item

    def upsert_open_alert(self, update, reason: str) -> dict[str, object]:
        alert = {
            "alert_id": "alert-123",
            "sku": update.sku,
            "name": update.name,
            "quantity": update.quantity,
            "reorder_threshold": update.reorder_threshold,
            "reason": reason,
            "status": "OPEN",
        }
        self.alerts.append(alert)
        return alert

    def resolve_open_alerts(self, sku: str) -> int:
        return 0

    def record_notification(self, alert: dict[str, object]) -> dict[str, object]:
        notification = {
            "notification_id": "notification-123",
            "alert_id": alert["alert_id"],
            "sku": alert["sku"],
        }
        self.notifications.append(notification)
        return notification

    def mark_alert_notified(self, alert_id: str) -> None:
        self.notified_alerts.append(alert_id)


def fake_context() -> SimpleNamespace:
    return SimpleNamespace(
        settings=FakeSettings(),
        aws=SimpleNamespace(sns=FakeSns()),
        cache=FakeCache(),
        storage=FakeStorage(),
    )


def test_inventory_worker_creates_alert_event_for_low_stock() -> None:
    context = fake_context()
    event = {
        "payload": {
            "sku": "GUMMY-001",
            "name": "Sour Gummy Worms",
            "quantity": 8,
            "reorder_threshold": 10,
        }
    }

    result = process_inventory_event(event, context)

    assert result == "ALERT_OPENED"
    assert context.storage.inventory[0]["status"] == "REORDER_NEEDED"
    assert context.storage.alerts[0]["sku"] == "GUMMY-001"
    assert context.aws.sns.published[0]["TopicArn"] == FakeSettings.alert_topic_arn
    assert "alerts:open" in context.cache.deleted


def test_inventory_worker_rejects_wrong_event_type_before_side_effects() -> None:
    context = fake_context()
    event = {
        "event_type": "reorder.alert.opened",
        "payload": {
            "sku": "GUMMY-001",
            "name": "Sour Gummy Worms",
            "quantity": 8,
            "reorder_threshold": 10,
        },
    }

    try:
        process_inventory_event(event, context)
    except ValueError as error:
        assert "Unexpected inventory event_type" in str(error)
    else:
        raise AssertionError("wrong event type should fail")

    assert context.storage.inventory == []
    assert context.storage.alerts == []


def test_alert_notifier_records_notification_audit() -> None:
    context = fake_context()
    event = {
        "payload": {
            "alert_id": "alert-123",
            "sku": "GUMMY-001",
            "name": "Sour Gummy Worms",
            "quantity": 8,
            "reorder_threshold": 10,
        }
    }

    notification = process_alert_event(event, context)

    assert notification["notification_id"] == "notification-123"
    assert context.storage.notifications[0]["alert_id"] == "alert-123"
    assert context.storage.notified_alerts == ["alert-123"]


def test_alert_notifier_rejects_wrong_event_type_before_side_effects() -> None:
    context = fake_context()
    event = {
        "event_type": "inventory.updated",
        "payload": {
            "alert_id": "alert-123",
            "sku": "GUMMY-001",
        },
    }

    try:
        process_alert_event(event, context)
    except ValueError as error:
        assert "Unexpected alert event_type" in str(error)
    else:
        raise AssertionError("wrong event type should fail")

    assert context.storage.notifications == []
    assert context.storage.notified_alerts == []
