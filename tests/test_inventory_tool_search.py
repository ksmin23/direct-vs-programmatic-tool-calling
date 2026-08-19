from __future__ import annotations

import pytest

from ptc_benchmark.inventory_tool_search import (
    CATALOG_SIZES,
    REQUIRED_INVENTORY_TOOLS,
    build_inventory_tool_search_scenario,
)


@pytest.mark.parametrize("catalog_size", CATALOG_SIZES)
def test_tool_search_catalog_defers_every_function(catalog_size: int) -> None:
    scenario = build_inventory_tool_search_scenario(catalog_size=catalog_size)
    tools = scenario.tool_definitions("programmatic_tool_search")
    namespaces = [tool for tool in tools if tool["type"] == "namespace"]
    functions = [function for namespace in namespaces for function in namespace["tools"]]

    assert scenario.function_count == catalog_size
    assert len(namespaces) == catalog_size // 5
    assert all(function["defer_loading"] is True for function in functions)
    assert [tool["type"] for tool in tools[-2:]] == [
        "tool_search",
        "programmatic_tool_calling",
    ]


def test_tool_search_scenario_executes_only_required_inventory_tools() -> None:
    scenario = build_inventory_tool_search_scenario(catalog_size=20)
    sku = scenario.dataset.skus[0]

    for name in REQUIRED_INVENTORY_TOOLS:
        assert scenario.execute("inventory", name, {"sku": sku})["sku"] == sku
    with pytest.raises(ValueError, match="not executable"):
        scenario.execute("billing", "get_invoice", {"sku": sku})
