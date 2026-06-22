from inventory_reorder.decision import evaluate_reorder
from inventory_reorder.models import InventoryUpdate


def test_low_stock_creates_reorder_decision() -> None:
    update = InventoryUpdate(
        sku="gummy-001",
        name="Sour Gummy Worms",
        quantity=8,
        reorder_threshold=10,
    )

    decision = evaluate_reorder(update)

    assert update.sku == "GUMMY-001"
    assert decision.reorder_needed is True
    assert decision.status == "REORDER_NEEDED"


def test_healthy_stock_does_not_create_reorder_decision() -> None:
    update = InventoryUpdate(
        sku="CHOC-001",
        name="Dark Chocolate Bar",
        quantity=30,
        reorder_threshold=10,
    )

    decision = evaluate_reorder(update)

    assert decision.reorder_needed is False
    assert decision.status == "HEALTHY"
