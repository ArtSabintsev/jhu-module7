from __future__ import annotations

from typing import Any
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

from inventory_reorder.models import InventoryUpdate, JsonDict, utc_now_iso
from inventory_reorder.settings import Settings


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS inventory (
    sku TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    reorder_threshold INTEGER NOT NULL,
    vendor TEXT,
    status TEXT NOT NULL,
    event_id TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reorder_alerts (
    alert_id TEXT PRIMARY KEY,
    sku TEXT NOT NULL,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    reorder_threshold INTEGER NOT NULL,
    vendor TEXT,
    status TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    notified_at TEXT,
    resolved_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_reorder_alerts_sku_status
    ON reorder_alerts (sku, status);

CREATE UNIQUE INDEX IF NOT EXISTS idx_reorder_alerts_one_open_per_sku
    ON reorder_alerts (sku)
    WHERE status = 'OPEN';

CREATE TABLE IF NOT EXISTS notification_audit (
    notification_id TEXT PRIMARY KEY,
    alert_id TEXT NOT NULL,
    sku TEXT NOT NULL,
    channel TEXT NOT NULL,
    destination TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class PostgresInventoryStorage:
    def __init__(self, settings: Settings) -> None:
        settings.require("postgres_dsn")
        self.dsn = settings.postgres_dsn

    def initialize_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(SCHEMA_SQL)

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
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO inventory (
                    sku, name, quantity, reorder_threshold, vendor, status,
                    event_id, updated_at
                )
                VALUES (
                    %(sku)s, %(name)s, %(quantity)s, %(reorder_threshold)s,
                    %(vendor)s, %(status)s, %(event_id)s, %(updated_at)s
                )
                ON CONFLICT (sku) DO UPDATE SET
                    name = EXCLUDED.name,
                    quantity = EXCLUDED.quantity,
                    reorder_threshold = EXCLUDED.reorder_threshold,
                    vendor = EXCLUDED.vendor,
                    status = EXCLUDED.status,
                    event_id = EXCLUDED.event_id,
                    updated_at = EXCLUDED.updated_at
                """,
                item,
            )
        return item

    def get_inventory(self, sku: str) -> JsonDict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM inventory WHERE sku = %s",
                (sku.upper(),),
            ).fetchone()
        return dict(row) if row else None

    def list_inventory(self) -> list[JsonDict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM inventory ORDER BY sku").fetchall()
        return [dict(row) for row in rows]

    def list_open_alerts(self) -> list[JsonDict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM reorder_alerts
                WHERE status = 'OPEN'
                ORDER BY updated_at DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def upsert_open_alert(self, update: InventoryUpdate, reason: str) -> JsonDict:
        now = utc_now_iso()
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
        with self._connect() as conn:
            row = conn.execute(
                """
                INSERT INTO reorder_alerts (
                    alert_id, sku, name, quantity, reorder_threshold, vendor,
                    status, reason, created_at, updated_at, notified_at, resolved_at
                )
                VALUES (
                    %(alert_id)s, %(sku)s, %(name)s, %(quantity)s,
                    %(reorder_threshold)s, %(vendor)s, %(status)s, %(reason)s,
                    %(created_at)s, %(updated_at)s, %(notified_at)s, %(resolved_at)s
                )
                ON CONFLICT (sku) WHERE status = 'OPEN'
                DO UPDATE SET
                    name = EXCLUDED.name,
                    quantity = EXCLUDED.quantity,
                    reorder_threshold = EXCLUDED.reorder_threshold,
                    vendor = EXCLUDED.vendor,
                    reason = EXCLUDED.reason,
                    updated_at = EXCLUDED.updated_at
                RETURNING *
                """,
                item,
            ).fetchone()
        return dict(row)

    def resolve_open_alerts(self, sku: str) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE reorder_alerts
                SET status = 'RESOLVED', resolved_at = %s
                WHERE sku = %s AND status = 'OPEN'
                """,
                (utc_now_iso(), sku.upper()),
            )
            return cursor.rowcount or 0

    def mark_alert_notified(self, alert_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE reorder_alerts SET notified_at = %s WHERE alert_id = %s",
                (utc_now_iso(), alert_id),
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
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO notification_audit (
                    notification_id, alert_id, sku, channel, destination,
                    status, created_at
                )
                VALUES (
                    %(notification_id)s, %(alert_id)s, %(sku)s, %(channel)s,
                    %(destination)s, %(status)s, %(created_at)s
                )
                """,
                item,
            )
        return item

    def _connect(self) -> psycopg.Connection[Any]:
        return psycopg.connect(self.dsn, row_factory=dict_row)


def main() -> None:
    settings = Settings.from_env()
    storage = PostgresInventoryStorage(settings)
    storage.initialize_schema()
    print("Initialized PostgreSQL schema for jhu-module7.")
