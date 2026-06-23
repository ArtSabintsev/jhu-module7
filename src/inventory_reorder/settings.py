from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


@dataclass(frozen=True)
class Settings:
    app_backend: str = "aws"
    aws_region: str = "us-east-1"
    inventory_topic_arn: str = ""
    alert_topic_arn: str = ""
    inventory_queue_url: str = ""
    alert_queue_url: str = ""
    inventory_table: str = "jhu-module7-inventory"
    alert_table: str = "jhu-module7-reorder-alerts"
    notification_table: str = "jhu-module7-notification-audit"
    postgres_dsn: str = ""
    kafka_bootstrap_servers: str = ""
    kafka_security_protocol: str = "SASL_SSL"
    kafka_sasl_mechanism: str = "SCRAM-SHA-256"
    kafka_username: str = ""
    kafka_password: str = ""
    kafka_ssl_cafile: str = ""
    kafka_ssl_certfile: str = ""
    kafka_ssl_keyfile: str = ""
    kafka_inventory_topic: str = "inventory-updates"
    kafka_alert_topic: str = "reorder-alerts"
    kafka_inventory_group: str = "inventory-worker"
    kafka_alert_group: str = "alert-notifier"
    kafka_topic_partitions: int = 3
    kafka_topic_replication_factor: int = 1
    redis_url: str = ""
    cache_ttl_seconds: int = 60
    poll_wait_seconds: int = 20
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            app_backend=os.getenv("APP_BACKEND", "aws").lower(),
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
            postgres_dsn=os.getenv("POSTGRES_DSN", ""),
            kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", ""),
            kafka_security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL", "SASL_SSL"),
            kafka_sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM", "SCRAM-SHA-256"),
            kafka_username=os.getenv("KAFKA_USERNAME", ""),
            kafka_password=os.getenv("KAFKA_PASSWORD", ""),
            kafka_ssl_cafile=os.getenv("KAFKA_SSL_CAFILE", ""),
            kafka_ssl_certfile=os.getenv("KAFKA_SSL_CERTFILE", ""),
            kafka_ssl_keyfile=os.getenv("KAFKA_SSL_KEYFILE", ""),
            kafka_inventory_topic=os.getenv("KAFKA_INVENTORY_TOPIC", "inventory-updates"),
            kafka_alert_topic=os.getenv("KAFKA_ALERT_TOPIC", "reorder-alerts"),
            kafka_inventory_group=os.getenv("KAFKA_INVENTORY_GROUP", "inventory-worker"),
            kafka_alert_group=os.getenv("KAFKA_ALERT_GROUP", "alert-notifier"),
            kafka_topic_partitions=_int_env("KAFKA_TOPIC_PARTITIONS", 3),
            kafka_topic_replication_factor=_int_env("KAFKA_TOPIC_REPLICATION_FACTOR", 1),
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

    @property
    def is_vultr(self) -> bool:
        return self.app_backend == "vultr"

    @property
    def is_aws(self) -> bool:
        return self.app_backend == "aws"
