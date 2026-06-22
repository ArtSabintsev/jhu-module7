from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import uuid4

from inventory_reorder.models import InventoryUpdate, JsonDict, utc_now_iso
from inventory_reorder.settings import Settings


def _clean(value: Any) -> Any:
    if isinstance(value, list):
        return [_clean(item) for item in value]
    if isinstance(value, dict):
        return {key: _clean(item) for key, item in value.items()}
    if isinstance(value, Decimal):
        if value % 1 == 0:
            return int(value)
        return float(value)
    return value


class InventoryStorage:
    def __init__(self, settings: Settings, dynamodb_resource: Any) -> None:
        self.inventory = dynamodb_resource.Table(settings.inventory_table)
        self.alerts = dynamodb_resource.Table(settings.alert_table)
        self.notifications = dynamodb_resource.Table(settings.notification_table)

    def put_inventory(self, update: InventoryUpdate, status: str) -> JsonDict:
        item = {
            "sku": update.sku,
            "name": update.name,
            "quantity": update.quantity,
            "reorder_threshold": update.reorder_threshold,
            "vendor": update.vendor,
            "status": status,
            "event_id": update.event_id,
            "updated_at": utc_now_iso(),
        }
        self.inventory.put_item(Item=item)
        return item

    def get_inventory(self, sku: str) -> JsonDict | None:
        response = self.inventory.get_item(Key={"sku": sku.upper()})
        item = response.get("Item")
        if item is None:
            return None
        return _clean(item)

    def list_inventory(self) -> list[JsonDict]:
        response = self.inventory.scan()
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = self.inventory.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))
        return sorted((_clean(item) for item in items), key=lambda item: item["sku"])

    def list_open_alerts(self) -> list[JsonDict]:
        items = self._scan_alerts()
        open_items = [item for item in items if item.get("status") == "OPEN"]
        return sorted(open_items, key=lambda item: item["updated_at"], reverse=True)

    def upsert_open_alert(self, update: InventoryUpdate, reason: str) -> JsonDict:
        now = utc_now_iso()
        existing = self._find_open_alert(update.sku)
        if existing is None:
            item = {
                "alert_id": str(uuid4()),
                "sku": update.sku,
                "name": update.name,
                "quantity": update.quantity,
                "reorder_threshold": update.reorder_threshold,
                "vendor": update.vendor,
                "status": "OPEN",
                "reason": reason,
                "created_at": now,
                "updated_at": now,
                "notified_at": None,
                "resolved_at": None,
            }
            self.alerts.put_item(Item=item)
            return item

        self.alerts.update_item(
            Key={"alert_id": existing["alert_id"]},
            UpdateExpression=(
                "SET #name = :name, quantity = :quantity, "
                "reorder_threshold = :threshold, vendor = :vendor, "
                "reason = :reason, updated_at = :updated_at"
            ),
            ExpressionAttributeNames={"#name": "name"},
            ExpressionAttributeValues={
                ":name": update.name,
                ":quantity": update.quantity,
                ":threshold": update.reorder_threshold,
                ":vendor": update.vendor,
                ":reason": reason,
                ":updated_at": now,
            },
        )
        existing.update(
            {
                "name": update.name,
                "quantity": update.quantity,
                "reorder_threshold": update.reorder_threshold,
                "vendor": update.vendor,
                "reason": reason,
                "updated_at": now,
            }
        )
        return existing

    def resolve_open_alerts(self, sku: str) -> int:
        now = utc_now_iso()
        resolved = 0
        for item in self._scan_alerts():
            if item.get("sku") != sku.upper() or item.get("status") != "OPEN":
                continue
            self.alerts.update_item(
                Key={"alert_id": item["alert_id"]},
                UpdateExpression="SET #status = :status, resolved_at = :resolved_at",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": "RESOLVED",
                    ":resolved_at": now,
                },
            )
            resolved += 1
        return resolved

    def mark_alert_notified(self, alert_id: str) -> None:
        self.alerts.update_item(
            Key={"alert_id": alert_id},
            UpdateExpression="SET notified_at = :notified_at",
            ExpressionAttributeValues={":notified_at": utc_now_iso()},
        )

    def record_notification(
        self,
        alert: JsonDict,
        channel: str = "manager-dashboard",
        destination: str = "store-manager",
    ) -> JsonDict:
        item = {
            "notification_id": str(uuid4()),
            "alert_id": alert["alert_id"],
            "sku": alert["sku"],
            "channel": channel,
            "destination": destination,
            "status": "RECORDED",
            "created_at": utc_now_iso(),
        }
        self.notifications.put_item(Item=item)
        return item

    def _scan_alerts(self) -> list[JsonDict]:
        response = self.alerts.scan()
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = self.alerts.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))
        return [_clean(item) for item in items]

    def _find_open_alert(self, sku: str) -> JsonDict | None:
        normalized = sku.upper()
        for item in self._scan_alerts():
            if item.get("sku") == normalized and item.get("status") == "OPEN":
                return item
        return None
