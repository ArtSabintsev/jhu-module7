from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class InventoryUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    sku: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    name: str = Field(min_length=1, max_length=128)
    quantity: int = Field(ge=0)
    reorder_threshold: int = Field(ge=0)
    vendor: str | None = Field(default=None, max_length=128)
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    received_at: str = Field(default_factory=utc_now_iso)

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, value: str) -> str:
        return value.upper()


class InventoryRecord(BaseModel):
    sku: str
    name: str
    quantity: int
    reorder_threshold: int
    vendor: str | None = None
    status: str
    event_id: str
    updated_at: str


class ReorderDecision(BaseModel):
    sku: str
    reorder_needed: bool
    status: str
    reason: str
    evaluated_at: str = Field(default_factory=utc_now_iso)


class ReorderAlert(BaseModel):
    alert_id: str
    sku: str
    name: str
    quantity: int
    reorder_threshold: int
    vendor: str | None = None
    status: str = "OPEN"
    reason: str
    created_at: str
    updated_at: str
    notified_at: str | None = None
    resolved_at: str | None = None


class NotificationAudit(BaseModel):
    notification_id: str
    alert_id: str
    sku: str
    channel: str
    destination: str
    status: str
    created_at: str = Field(default_factory=utc_now_iso)


class AcceptedResponse(BaseModel):
    status: str
    message_id: str
    event_id: str


JsonDict = dict[str, Any]
