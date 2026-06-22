from __future__ import annotations

import logging
from functools import lru_cache

import uvicorn
from fastapi import FastAPI, HTTPException

from inventory_reorder.messages import inventory_event, publish_json
from inventory_reorder.models import AcceptedResponse, InventoryUpdate
from inventory_reorder.runtime import AppContext
from inventory_reorder.settings import Settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_context() -> AppContext:
    return AppContext()


def create_app() -> FastAPI:
    app = FastAPI(
        title="JHU Module 7 Inventory Reorder API",
        version="0.1.0",
        description="API process for the distributed inventory reorder workflow.",
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "inventory-api"}

    @app.post("/inventory", status_code=202, response_model=AcceptedResponse)
    def submit_inventory(update: InventoryUpdate) -> AcceptedResponse:
        context = get_context()
        context.settings.require("inventory_topic_arn")
        message_id = publish_json(
            context.aws.sns,
            context.settings.inventory_topic_arn,
            f"Inventory update {update.sku}",
            inventory_event(update),
        )
        logger.info("accepted inventory update sku=%s event_id=%s", update.sku, update.event_id)
        return AcceptedResponse(
            status="ACCEPTED",
            message_id=message_id,
            event_id=update.event_id,
        )

    @app.get("/inventory")
    def list_inventory() -> dict[str, object]:
        context = get_context()
        cache_key = "inventory:all"
        cached = context.cache.get_json(cache_key)
        if cached is not None:
            return {"cache": "HIT", "items": cached}

        items = context.storage.list_inventory()
        context.cache.set_json(cache_key, items)
        return {"cache": "MISS", "items": items}

    @app.get("/inventory/{sku}")
    def get_inventory(sku: str) -> dict[str, object]:
        context = get_context()
        normalized = sku.upper()
        cache_key = f"inventory:{normalized}"
        cached = context.cache.get_json(cache_key)
        if cached is not None:
            return {"cache": "HIT", "item": cached}

        item = context.storage.get_inventory(normalized)
        if item is None:
            raise HTTPException(status_code=404, detail=f"SKU not found: {normalized}")
        context.cache.set_json(cache_key, item)
        return {"cache": "MISS", "item": item}

    @app.get("/alerts")
    def list_alerts() -> dict[str, object]:
        context = get_context()
        cache_key = "alerts:open"
        cached = context.cache.get_json(cache_key)
        if cached is not None:
            return {"cache": "HIT", "items": cached}

        items = context.storage.list_open_alerts()
        context.cache.set_json(cache_key, items)
        return {"cache": "MISS", "items": items}

    return app


app = create_app()


def main() -> None:
    settings = Settings.from_env()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    uvicorn.run("inventory_reorder.api:app", host=settings.api_host, port=settings.api_port)


if __name__ == "__main__":
    main()
