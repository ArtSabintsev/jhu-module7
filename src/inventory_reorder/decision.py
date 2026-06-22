from __future__ import annotations

from inventory_reorder.models import InventoryUpdate, ReorderDecision, utc_now_iso


def evaluate_reorder(update: InventoryUpdate) -> ReorderDecision:
    if update.quantity <= update.reorder_threshold:
        return ReorderDecision(
            sku=update.sku,
            reorder_needed=True,
            status="REORDER_NEEDED",
            reason=(
                f"Quantity {update.quantity} is at or below reorder threshold "
                f"{update.reorder_threshold}."
            ),
            evaluated_at=utc_now_iso(),
        )

    return ReorderDecision(
        sku=update.sku,
        reorder_needed=False,
        status="HEALTHY",
        reason=(
            f"Quantity {update.quantity} is above reorder threshold "
            f"{update.reorder_threshold}."
        ),
        evaluated_at=utc_now_iso(),
    )
