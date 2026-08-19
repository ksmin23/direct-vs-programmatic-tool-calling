from __future__ import annotations

from ptc_benchmark.runner import ToolCallingRun
from ptc_trace_demo.inventory_trace import (
    InventoryTraceComparison,
    TraceEvent,
    configure_trace_error_logging,
)


def test_trace_comparison_exposes_normalized_timeline() -> None:
    run = ToolCallingRun(
        arm="direct",
        run_id="run-1",
        model="test",
        scenario="inventory",
        case_id="inventory-small",
        prompt_cache_key="cache-key",
    )
    comparison = InventoryTraceComparison(
        comparison_id="comparison-1",
        trace_id=None,
        runs={"direct": run},
        events=(
            TraceEvent(
                sequence=1,
                arm="direct",
                kind="function_call",
                name="get_inventory",
                elapsed_seconds=0.0123,
                duration_seconds=0.0044,
                request_index=0,
                response_id="response-1",
                call_id="call-1",
                caller={"caller_id": "program-1"},
                payload_bytes=42,
                payload=None,
            ),
        ),
    )

    assert comparison.timeline_rows() == [
        {
            "sequence": 1,
            "arm": "direct",
            "elapsed_ms": 12.3,
            "duration_ms": 4.4,
            "event": "function_call",
            "name": "get_inventory",
            "request": 1,
            "response_id": "response-1",
            "call_id": "call-1",
            "caller_id": "program-1",
            "payload_bytes": 42,
        }
    ]


def test_trace_error_logging_is_redacted_by_default(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_AGENTS_DONT_LOG_MODEL_DATA", raising=False)
    monkeypatch.delenv("OPENAI_AGENTS_DONT_LOG_TOOL_DATA", raising=False)

    configure_trace_error_logging(show_details=False)

    import os

    assert os.environ["OPENAI_AGENTS_DONT_LOG_MODEL_DATA"] == "1"
    assert os.environ["OPENAI_AGENTS_DONT_LOG_TOOL_DATA"] == "1"
