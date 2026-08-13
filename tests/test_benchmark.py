from __future__ import annotations

from types import SimpleNamespace

import pytest

from ptc_benchmark.incident import INCIDENT_CASE_IDS, build_incident_scenario
from ptc_benchmark.inventory import SCALE_COUNTS, build_inventory_dataset
from ptc_benchmark.pricing import ModelPrice, PricingCatalog, estimate_usage_cost
from ptc_benchmark.refund import build_refund_approval, build_refund_selection
from ptc_benchmark.runner import RunConfig, ToolCallingRunner, Usage, parse_result_json


@pytest.mark.parametrize("scale,count", SCALE_COUNTS.items())
def test_inventory_fixture_and_oracle(scale: str, count: int) -> None:
    dataset = build_inventory_dataset(scale)

    assert len(dataset.skus) == count
    assert dataset.expected_plan()["total_reorder_units"] > 0
    assert len(dataset.tool_definitions("direct")) == 3
    assert dataset.tool_definitions("programmatic")[-1] == {
        "type": "programmatic_tool_calling"
    }

    sku = dataset.skus[0]
    assert dataset.execute("get_inventory", {"sku": sku})["sku"] == sku
    with pytest.raises(ValueError, match="Unknown sku"):
        dataset.execute("get_inventory", {"sku": "missing"})


@pytest.mark.parametrize("case_id", INCIDENT_CASE_IDS)
def test_incident_fixtures(case_id: str) -> None:
    scenario = build_incident_scenario(case_id)
    expected = scenario.expected_result()

    assert expected["incident_id"] == case_id
    assert expected["confidence"] == "high"
    assert len(expected["evidence_ids"]) >= 3
    assert len(scenario.tool_definitions("direct")) == 4
    assert len(scenario.tool_definitions("programmatic")) == 5


@pytest.mark.parametrize(
    ("scale", "candidate_ids"),
    [
        ("small", ["ord-001", "ord-003"]),
        ("medium", ["ord-001", "ord-003", "ord-005"]),
        ("large", ["ord-001", "ord-003", "ord-005", "ord-007"]),
    ],
)
def test_refund_selection_and_approval(scale: str, candidate_ids: list[str]) -> None:
    selection = build_refund_selection(scale)
    plan = selection.expected_selection()

    assert [row["order_id"] for row in plan["candidates"]] == candidate_ids
    approval = build_refund_approval(selection)
    result = approval.expected_result()
    assert all(row["status"] == "issued" for row in result["refunds"])
    assert result["total_issued_cents"] == sum(
        row["refund_amount_cents"] for row in result["refunds"]
    )


def test_result_parser_and_pricing() -> None:
    assert parse_result_json('prefix RESULT_JSON: {"ok":true}\nEXPLANATION: done') == {
        "ok": True
    }
    assert parse_result_json("no marker") is None

    catalog = PricingCatalog(
        effective_date="2026-01-01",
        source_url="https://example.test/pricing",
        models={"test": ModelPrice(2.0, 0.5, 1.0, 8.0)},
    )
    estimate = estimate_usage_cost(
        Usage(
            input_tokens=1_000_000,
            cached_input_tokens=200_000,
            cache_write_input_tokens=100_000,
            output_tokens=250_000,
        ),
        "test",
        catalog,
    )
    assert estimate.uncached_input_tokens == 700_000
    assert estimate.total_cost == pytest.approx(3.6)


class _FakeResponses:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **request: object) -> SimpleNamespace:
        self.calls.append(request)
        if len(self.calls) == 1:
            sku = build_inventory_dataset("small").skus[0]
            return SimpleNamespace(
                id="response-1",
                status="completed",
                output=[
                    {
                        "type": "function_call",
                        "name": "get_inventory",
                        "call_id": "call-1",
                        "arguments": f'{{"sku":"{sku}"}}',
                        "caller": {"type": "direct"},
                    }
                ],
                usage=None,
                output_text="",
            )
        return SimpleNamespace(
            id="response-2",
            status="completed",
            output=[{"type": "message"}],
            usage=None,
            output_text='RESULT_JSON: {"recommendations":[],"total_reorder_units":0}',
        )


def test_runner_dispatches_tool_output_without_network() -> None:
    responses = _FakeResponses()
    client = SimpleNamespace(responses=responses)
    dataset = build_inventory_dataset("small")

    run = ToolCallingRunner(client).run(
        arm="direct",
        scenario=dataset,
        config=RunConfig(model="test", max_requests=2),
        run_id="offline-test",
    )

    assert len(run.requests) == 2
    assert len(run.tool_calls) == 1
    assert run.tool_calls[0].name == "get_inventory"
    second_input = responses.calls[1]["input"]
    assert isinstance(second_input, list)
    assert any(item.get("type") == "function_call_output" for item in second_input)
    assert run.parsed_final_result == {
        "recommendations": [],
        "total_reorder_units": 0,
    }
