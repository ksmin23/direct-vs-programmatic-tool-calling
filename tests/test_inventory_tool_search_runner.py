from __future__ import annotations

from types import SimpleNamespace

from ptc_benchmark.inventory_tool_search import build_inventory_tool_search_scenario
from ptc_benchmark.inventory_tool_search_runner import (
    InventoryToolSearchRunner,
    ToolSearchRunConfig,
    build_tool_search_cache_key,
    comparison_order,
    semantic_timeline,
)


class _ToolSearchResponses:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **request: object) -> SimpleNamespace:
        self.calls.append(request)
        inventory_namespace = next(
            tool for tool in request["tools"] if tool["type"] == "namespace"
        )
        return SimpleNamespace(
            id="response-1",
            status="completed",
            output=[
                {"type": "tool_search_call", "arguments": {"paths": ["inventory"]}},
                {"type": "tool_search_output", "tools": [inventory_namespace]},
                {"type": "message"},
            ],
            usage=None,
            output_text='RESULT_JSON: {"recommendations":[],"total_reorder_units":0}',
        )


def test_tool_search_runner_uses_explicit_cache_boundary_and_records_loaded_tools() -> None:
    responses = _ToolSearchResponses()
    scenario = build_inventory_tool_search_scenario(catalog_size=20)

    run = InventoryToolSearchRunner(SimpleNamespace(responses=responses)).run(
        arm="programmatic_tool_search",
        scenario=scenario,
        config=ToolSearchRunConfig(model="test", max_requests=1),
        experiment_id="cache-test",
        repetition=2,
    )

    request = responses.calls[0]
    assert request["prompt_cache_options"] == {"mode": "explicit"}
    assert request["input"][0]["content"][0]["prompt_cache_breakpoint"] == {
        "mode": "explicit"
    }
    assert run.loaded_tools == {
        f"inventory.{tool['name']}" for tool in scenario.namespaces[0]["tools"]
    }
    assert [row["type"] for row in semantic_timeline(run)] == [
        "tool_search_call",
        "tool_search_output",
        "message",
    ]


def test_tool_search_comparison_order_and_cache_keys_are_isolated() -> None:
    assert comparison_order(1) == ("programmatic_eager", "programmatic_tool_search")
    assert comparison_order(2) == ("programmatic_tool_search", "programmatic_eager")
    assert build_tool_search_cache_key(
        experiment_id="test",
        catalog_size=100,
        arm="programmatic_eager",
        repetition=1,
    ) != build_tool_search_cache_key(
        experiment_id="test",
        catalog_size=100,
        arm="programmatic_tool_search",
        repetition=1,
    )
