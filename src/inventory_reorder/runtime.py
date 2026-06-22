from __future__ import annotations

from inventory_reorder.aws import AwsClients
from inventory_reorder.cache import InventoryCache
from inventory_reorder.settings import Settings
from inventory_reorder.storage import InventoryStorage


class AppContext:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()
        self.aws = AwsClients(self.settings)
        self.cache = InventoryCache.from_settings(self.settings)
        self.storage = InventoryStorage(self.settings, self.aws.dynamodb)
