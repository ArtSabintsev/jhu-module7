from __future__ import annotations

from inventory_reorder.aws import AwsClients
from inventory_reorder.cache import InventoryCache
from inventory_reorder.postgres_storage import PostgresInventoryStorage
from inventory_reorder.settings import Settings
from inventory_reorder.storage import InventoryStorage
from inventory_reorder.vultr_messaging import KafkaEventBus


class AppContext:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()
        self.cache = InventoryCache.from_settings(self.settings)
        self.aws: AwsClients | None = None
        self.kafka: KafkaEventBus | None = None

        if self.settings.is_aws:
            self.aws = AwsClients(self.settings)
            self.storage = InventoryStorage(self.settings, self.aws.dynamodb)
            return

        if self.settings.is_vultr:
            self.kafka = KafkaEventBus(self.settings)
            self.storage = PostgresInventoryStorage(self.settings)
            return

        raise RuntimeError(f"Unsupported APP_BACKEND: {self.settings.app_backend}")
