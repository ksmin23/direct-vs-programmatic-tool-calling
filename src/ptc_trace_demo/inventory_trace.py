from __future__ import annotations

import json
import os
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from typing import Any, Iterator, Mapping

from ptc_benchmark.inventory import Arm, InventoryDataset, compact_json
from ptc_benchmark.runner import RunConfig, ToolCallingRun, ToolCallingRunner


def configure_trace_error_logging(*, show_details: bool) -> None:
    """Toggle detailed Agents SDK trace-export errors for notebook debugging.

    The SDK reads these environment variables when ``agents._debug`` is imported.
    Updating an already-loaded debug module makes the toggle effective when a
    notebook cell is rerun without restarting its kernel.
    """
    redact_data = not show_details
    flag_value = "1" if redact_data else "0"
    os.environ["OPENAI_AGENTS_DONT_LOG_MODEL_DATA"] = flag_value
    os.environ["OPENAI_AGENTS_DONT_LOG_TOOL_DATA"] = flag_value

    debug_module = sys.modules.get("agents._debug")
    if debug_module is not None:
        debug_module.DONT_LOG_MODEL_DATA = redact_data
        debug_module.DONT_LOG_TOOL_DATA = redact_data


@dataclass(frozen=True)
class TraceEvent:
    sequence: int
    arm: Arm
    kind: str
    name: str
    elapsed_seconds: float
    duration_seconds: float
    request_index: int | None
    response_id: str | None
    call_id: str | None
    caller: dict[str, Any] | None
    payload_bytes: int
    payload: Any | None


@dataclass(frozen=True)
class InventoryTraceComparison:
    comparison_id: str
    trace_id: str | None
    runs: dict[Arm, ToolCallingRun]
    events: tuple[TraceEvent, ...]

    def timeline_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "sequence": event.sequence,
                "arm": event.arm,
                "elapsed_ms": round(event.elapsed_seconds * 1_000, 1),
                "duration_ms": round(event.duration_seconds * 1_000, 1),
                "event": event.kind,
                "name": event.name,
                "request": event.request_index + 1 if event.request_index is not None else None,
                "response_id": event.response_id,
                "call_id": event.call_id,
                "caller_id": (event.caller or {}).get("caller_id"),
                "payload_bytes": event.payload_bytes,
            }
            for event in self.events
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "comparison_id": self.comparison_id,
            "trace_id": self.trace_id,
            "runs": {arm: run.to_dict() for arm, run in self.runs.items()},
            "events": [asdict(event) for event in self.events],
        }


class _EventRecorder:
    def __init__(self, *, include_payloads: bool):
        self.include_payloads = include_payloads
        self.started = time.perf_counter()
        self.events: list[TraceEvent] = []

    def record(
        self,
        *,
        arm: Arm,
        kind: str,
        name: str,
        payload: Any,
        duration_seconds: float = 0.0,
        request_index: int | None = None,
        response_id: str | None = None,
        call_id: str | None = None,
        caller: dict[str, Any] | None = None,
    ) -> None:
        normalized = _jsonable(payload)
        encoded = compact_json(normalized).encode("utf-8")
        self.events.append(
            TraceEvent(
                sequence=len(self.events) + 1,
                arm=arm,
                kind=kind,
                name=name,
                elapsed_seconds=time.perf_counter() - self.started,
                duration_seconds=duration_seconds,
                request_index=request_index,
                response_id=response_id,
                call_id=call_id,
                caller=caller,
                payload_bytes=len(encoded),
                payload=normalized if self.include_payloads else None,
            )
        )

    def trace_summary(self, summary: Mapping[str, Any]) -> dict[str, Any]:
        """Return bounded, non-sensitive data suitable for an OpenAI custom span."""
        return _jsonable(summary)


class _TracingResponses:
    def __init__(
        self,
        responses: Any,
        *,
        arm: Arm,
        recorder: _EventRecorder,
        export_openai_trace: bool,
        pending_calls: list[dict[str, Any]],
    ):
        self._responses = responses
        self._arm = arm
        self._recorder = recorder
        self._export_openai_trace = export_openai_trace
        self._pending_calls = pending_calls
        self._request_index = 0

    def create(self, **kwargs: Any) -> Any:
        request_index = self._request_index
        self._request_index += 1
        request_payload = _jsonable(kwargs)
        trace_data = self._recorder.trace_summary(
            {
                "arm": self._arm,
                "request": request_index + 1,
                "model": kwargs.get("model"),
                "input_items": len(kwargs.get("input", [])),
                "tools": len(kwargs.get("tools", [])),
                "request_payload_bytes": len(compact_json(request_payload).encode("utf-8")),
            }
        )

        started = time.perf_counter()
        with _custom_span(self._export_openai_trace, "model_request", trace_data):
            response = self._responses.create(**kwargs)
            duration = time.perf_counter() - started
            response_id = str(_read(response, "id", ""))
            output_items = [_dump_item(item) for item in _read(response, "output", [])]
            response_payload = {
                "response_id": response_id,
                "status": _read(response, "status", "unknown"),
                "output": output_items,
                "usage": _jsonable(_read(response, "usage", None)),
            }
            trace_data.update(
                self._recorder.trace_summary(
                    {
                        "response_id": response_id,
                        "status": response_payload["status"],
                        "output_types": [item.get("type", "unknown") for item in output_items],
                        "response_payload_bytes": len(
                            compact_json(response_payload).encode("utf-8")
                        ),
                    }
                )
            )

        self._recorder.record(
            arm=self._arm,
            kind="model_request",
            name=f"request_{request_index + 1}",
            payload={"request": request_payload, "response": response_payload},
            duration_seconds=duration,
            request_index=request_index,
            response_id=response_id,
        )
        for item in output_items:
            self._record_output_item(item, request_index=request_index, response_id=response_id)
        return response

    def _record_output_item(
        self,
        item: dict[str, Any],
        *,
        request_index: int,
        response_id: str,
    ) -> None:
        item_type = str(item.get("type", "unknown"))
        call_id = _optional_string(item.get("call_id"))
        caller = item.get("caller") if isinstance(item.get("caller"), dict) else None
        if item_type == "function_call":
            queued_call = dict(item)
            queued_call["_trace_request_index"] = request_index
            self._pending_calls.append(queued_call)

        names = {
            "program": "generated_program",
            "function_call": str(item.get("name", "function")),
            "program_output": "program_output",
            "message": "final_assistant_message",
        }
        if item_type not in names:
            return

        data = self._recorder.trace_summary(
            {
                "arm": self._arm,
                "type": item_type,
                "name": names[item_type],
                "call_id": call_id,
                "caller": caller,
                "payload_bytes": len(compact_json(item).encode("utf-8")),
            }
        )
        with _custom_span(self._export_openai_trace, item_type, data):
            pass
        self._recorder.record(
            arm=self._arm,
            kind="assistant_message" if item_type == "message" else item_type,
            name=names[item_type],
            payload=item,
            request_index=request_index,
            response_id=response_id,
            call_id=call_id,
            caller=caller,
        )


class _TracingClient:
    def __init__(
        self,
        client: Any,
        *,
        arm: Arm,
        recorder: _EventRecorder,
        export_openai_trace: bool,
        pending_calls: list[dict[str, Any]],
    ):
        self.responses = _TracingResponses(
            client.responses,
            arm=arm,
            recorder=recorder,
            export_openai_trace=export_openai_trace,
            pending_calls=pending_calls,
        )


class _TracingScenario:
    def __init__(
        self,
        scenario: InventoryDataset,
        *,
        arm: Arm,
        recorder: _EventRecorder,
        export_openai_trace: bool,
        pending_calls: list[dict[str, Any]],
    ):
        self._scenario = scenario
        self._arm = arm
        self._recorder = recorder
        self._export_openai_trace = export_openai_trace
        self._pending_calls = pending_calls
        self.scenario_name = scenario.scenario_name
        self.case_id = scenario.case_id
        self.scale = scenario.scale

    def prompt(self, arm: Arm) -> tuple[str, str]:
        return self._scenario.prompt(arm)

    def tool_definitions(self, arm: Arm) -> list[dict[str, Any]]:
        return self._scenario.tool_definitions(arm)

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        call = self._pop_call(tool_name, arguments)
        call_id = _optional_string(call.get("call_id"))
        caller = call.get("caller") if isinstance(call.get("caller"), dict) else None
        request_index = int(call["_trace_request_index"])
        span_input = self._recorder.trace_summary(
            {
                "arm": self._arm,
                "call_id": call_id,
                "caller": caller,
                "arguments_payload_bytes": len(compact_json(arguments).encode("utf-8")),
            }
        )
        started = time.perf_counter()
        with _function_span(
            self._export_openai_trace,
            tool_name,
            span_input,
        ) as span:
            output = self._scenario.execute(tool_name, arguments)
            if span is not None:
                span.span_data.output = compact_json(
                    self._recorder.trace_summary(
                        {
                            "arm": self._arm,
                            "payload_bytes": len(compact_json(output).encode("utf-8")),
                        }
                    )
                )
        self._recorder.record(
            arm=self._arm,
            kind="tool_output",
            name=tool_name,
            payload={
                "arguments": arguments,
                "output": output,
                "call_id": call_id,
                "caller": caller,
            },
            duration_seconds=time.perf_counter() - started,
            request_index=request_index,
            call_id=call_id,
            caller=caller,
        )
        return output

    def _pop_call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        for index, call in enumerate(self._pending_calls):
            if call.get("name") != tool_name:
                continue
            if json.loads(str(call.get("arguments", "{}"))) == arguments:
                return self._pending_calls.pop(index)
        raise RuntimeError(f"Trace adapter could not match pending call for {tool_name}")


def run_inventory_trace_comparison(
    *,
    client: Any,
    dataset: InventoryDataset,
    config: RunConfig | None = None,
    comparison_id: str | None = None,
    export_openai_trace: bool = False,
    include_payloads: bool = True,
) -> InventoryTraceComparison:
    config = config or RunConfig()
    comparison_id = comparison_id or f"inventory-trace-{uuid.uuid4().hex[:12]}"
    recorder = _EventRecorder(include_payloads=include_payloads)
    runs: dict[Arm, ToolCallingRun] = {}

    with _comparison_trace(
        enabled=export_openai_trace,
        comparison_id=comparison_id,
        model=config.model,
        scale=dataset.scale,
        include_payloads=include_payloads,
    ) as trace_id:
        for arm in ("direct", "programmatic"):
            pending_calls: list[dict[str, Any]] = []
            with _arm_span(
                enabled=export_openai_trace,
                arm=arm,
                comparison_id=comparison_id,
                model=config.model,
            ):
                traced_client = _TracingClient(
                    client,
                    arm=arm,
                    recorder=recorder,
                    export_openai_trace=export_openai_trace,
                    pending_calls=pending_calls,
                )
                traced_scenario = _TracingScenario(
                    dataset,
                    arm=arm,
                    recorder=recorder,
                    export_openai_trace=export_openai_trace,
                    pending_calls=pending_calls,
                )
                runs[arm] = ToolCallingRunner(traced_client).run(
                    arm=arm,
                    scenario=traced_scenario,
                    config=config,
                    run_id=f"{comparison_id}-{arm}",
                )

    return InventoryTraceComparison(
        comparison_id=comparison_id,
        trace_id=trace_id,
        runs=runs,
        events=tuple(recorder.events),
    )


@contextmanager
def _comparison_trace(
    *,
    enabled: bool,
    comparison_id: str,
    model: str,
    scale: str,
    include_payloads: bool,
) -> Iterator[str | None]:
    if not enabled:
        yield None
        return

    try:
        from agents.tracing import flush_traces, trace
    except ImportError as exc:
        raise RuntimeError(
            "OpenAI Trace export requires the trace extra: uv sync --extra dev --extra trace"
        ) from exc

    with trace(
        "Direct vs Programmatic Tool Calling - Inventory",
        group_id=comparison_id,
        metadata={
            "comparison_id": comparison_id,
            "scenario": "inventory_replenishment",
            "model": model,
            "scale": scale,
            "local_payloads_included": "true" if include_payloads else "false",
            "trace_payload_mode": "summary",
        },
    ) as current_trace:
        yield current_trace.trace_id
    flush_traces()


@contextmanager
def _arm_span(
    *,
    enabled: bool,
    arm: Arm,
    comparison_id: str,
    model: str,
) -> Iterator[None]:
    with _custom_span(
        enabled,
        f"{arm}_arm",
        {"arm": arm, "comparison_id": comparison_id, "model": model},
    ):
        yield


@contextmanager
def _custom_span(enabled: bool, name: str, data: dict[str, Any]) -> Iterator[Any | None]:
    if not enabled:
        yield None
        return
    from agents.tracing import custom_span

    with custom_span(name, data=data) as span:
        yield span


@contextmanager
def _function_span(
    enabled: bool,
    name: str,
    input_payload: dict[str, Any],
) -> Iterator[Any | None]:
    if not enabled:
        yield None
        return
    from agents.tracing import function_span

    with function_span(name, input=compact_json(input_payload)) as span:
        yield span


def _dump_item(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        return item
    model_dump = getattr(item, "model_dump", None)
    if callable(model_dump):
        return model_dump(exclude_none=True)
    raise TypeError(f"Cannot serialize response item of type {type(item)!r}")


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return _jsonable(model_dump(exclude_none=True))
    return str(value)


def _read(value: Any, name: str, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _optional_string(value: Any) -> str | None:
    return str(value) if value is not None else None
