from __future__ import annotations

import pytest

from ptc_benchmark.inventory import SCALE_COUNTS, build_inventory_dataset


@pytest.mark.parametrize("scale,count", SCALE_COUNTS.items())
def test_inventory_dataset_exposes_deterministic_oracle(scale: str, count: int) -> None:
    dataset = build_inventory_dataset(scale)

    assert len(dataset.skus) == count
    assert dataset.expected_plan()["total_reorder_units"] > 0
    assert len(dataset.tool_definitions("direct")) == 3
    assert dataset.tool_definitions("programmatic")[-1] == {
        "type": "programmatic_tool_calling"
    }


def test_inventory_dataset_rejects_unknown_sku() -> None:
    dataset = build_inventory_dataset("small")

    with pytest.raises(ValueError, match="Unknown sku"):
        dataset.execute("get_inventory", {"sku": "missing"})
