from __future__ import annotations

import os
from dataclasses import dataclass


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


@dataclass(frozen=True)
class Settings:
    aws_region: str = "us-east-1"
    inventory_topic_arn: str = ""
    alert_topic_arn: str = ""
    inventory_queue_url: str = ""
    alert_queue_url: str = ""
    inventory_table: str = "jhu-module7-inventory"
    alert_table: str = "jhu-module7-reorder-alerts"
    notification_table: str = "jhu-module7-notification-audit"
    redis_url: str = ""
    cache_ttl_seconds: int = 60
    poll_wait_seconds: int = 20
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
            inventory_topic_arn=os.getenv("INVENTORY_TOPIC_ARN", ""),
            alert_topic_arn=os.getenv("ALERT_TOPIC_ARN", ""),
            inventory_queue_url=os.getenv("INVENTORY_QUEUE_URL", ""),
            alert_queue_url=os.getenv("ALERT_QUEUE_URL", ""),
            inventory_table=os.getenv("INVENTORY_TABLE", "jhu-module7-inventory"),
            alert_table=os.getenv("ALERT_TABLE", "jhu-module7-reorder-alerts"),
            notification_table=os.getenv(
                "NOTIFICATION_TABLE", "jhu-module7-notification-audit"
            ),
            redis_url=os.getenv("REDIS_URL", ""),
            cache_ttl_seconds=_int_env("CACHE_TTL_SECONDS", 60),
            poll_wait_seconds=_int_env("POLL_WAIT_SECONDS", 20),
            api_host=os.getenv("API_HOST", "0.0.0.0"),
            api_port=_int_env("API_PORT", 8000),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

    def require(self, *names: str) -> None:
        missing = [name for name in names if not getattr(self, name)]
        if missing:
            formatted = ", ".join(missing)
            raise RuntimeError(f"Missing required settings: {formatted}")
