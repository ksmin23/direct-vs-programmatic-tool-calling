from __future__ import annotations

from types import SimpleNamespace

from ptc_benchmark.inventory import build_inventory_dataset
from ptc_benchmark.runner import InventoryRunner, RunConfig, parse_result_json


class _InventoryResponses:
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


def test_inventory_runner_continues_with_function_output() -> None:
    responses = _InventoryResponses()
    runner = InventoryRunner(SimpleNamespace(responses=responses))

    run = runner.run(
        arm="direct",
        dataset=build_inventory_dataset("small"),
        config=RunConfig(model="test", max_requests=2),
        run_id="offline-test",
    )

    assert len(run.requests) == 2
    assert run.tool_calls[0].name == "get_inventory"
    second_input = responses.calls[1]["input"]
    assert isinstance(second_input, list)
    assert any(item.get("type") == "function_call_output" for item in second_input)
    assert run.parsed_final_result == {
        "recommendations": [],
        "total_reorder_units": 0,
    }


def test_result_parser_reads_only_result_json_payload() -> None:
    assert parse_result_json('prefix RESULT_JSON: {"ok":true}\nEXPLANATION: done') == {
        "ok": True
    }
    assert parse_result_json("no marker") is None
