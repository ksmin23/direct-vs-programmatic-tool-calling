from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol

from .inventory import Arm, InventoryDataset, compact_json


class ResponsesClient(Protocol):
    responses: Any


class ToolCallingScenario(Protocol):
    scenario_name: str
    case_id: str

    def prompt(self, arm: Arm) -> tuple[str, str]: ...

    def tool_definitions(self, arm: Arm) -> list[dict[str, Any]]: ...

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]: ...


@dataclass(frozen=True)
class RunConfig:
    model: str = "gpt-5.6"
    reasoning_effort: str = "low"
    max_output_tokens: int = 8_192
    max_requests: int = 16
    store: bool = False


@dataclass
class Usage:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    cache_write_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_output_tokens: int = 0
    total_tokens: int = 0

    def add(self, other: "Usage") -> None:
        for field_name in asdict(self):
            setattr(self, field_name, getattr(self, field_name) + getattr(other, field_name))


@dataclass(frozen=True)
class ToolCallRecord:
    request_index: int
    name: str
    call_id: str
    arguments: dict[str, Any]
    caller: dict[str, Any] | None
    output: dict[str, Any]


@dataclass(frozen=True)
class RequestRecord:
    request_index: int
    response_id: str
    status: str
    latency_seconds: float
    output_types: tuple[str, ...]
    usage: Usage
    output_items: tuple[dict[str, Any], ...]


@dataclass
class ToolCallingRun:
    arm: Arm
    run_id: str
    model: str
    scenario: str
    case_id: str
    prompt_cache_key: str
    scale: str | None = None
    requests: list[RequestRecord] = field(default_factory=list)
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    program_outputs: list[dict[str, Any]] = field(default_factory=list)
    generated_programs: list[str] = field(default_factory=list)
    final_output: str = ""
    parsed_final_result: dict[str, Any] | None = None
    total_latency_seconds: float = 0.0

    @property
    def usage(self) -> Usage:
        total = Usage()
        for request in self.requests:
            total.add(request.usage)
        return total

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ToolCallingRunner:
    def __init__(self, client: ResponsesClient):
        self.client = client

    def run(
        self,
        *,
        arm: Arm,
        scenario: ToolCallingScenario,
        config: RunConfig | None = None,
        run_id: str | None = None,
    ) -> ToolCallingRun:
        config = config or RunConfig()
        run_id = run_id or f"{scenario.scenario_name}-{uuid.uuid4().hex[:12]}"
        cache_key = _prompt_cache_key(scenario.scenario_name, run_id, arm)
        instructions, user_input = scenario.prompt(arm)
        input_items: list[Any] = [{"role": "user", "content": user_input}]
        tools = scenario.tool_definitions(arm)
        result = ToolCallingRun(
            arm=arm,
            run_id=run_id,
            model=config.model,
            scenario=scenario.scenario_name,
            case_id=scenario.case_id,
            prompt_cache_key=cache_key,
            scale=getattr(scenario, "scale", None),
        )
        task_started = time.perf_counter()

        for request_index in range(config.max_requests):
            request: dict[str, Any] = {
                "model": config.model,
                "instructions": instructions,
                "input": input_items,
                "tools": tools,
                "store": config.store,
                "parallel_tool_calls": True,
                "reasoning": {"effort": config.reasoning_effort},
                "max_output_tokens": config.max_output_tokens,
                "prompt_cache_key": cache_key,
            }
            if arm == "programmatic" and request_index == 0:
                request["tool_choice"] = {"type": "programmatic_tool_calling"}

            started = time.perf_counter()
            response = self.client.responses.create(**request)
            latency = time.perf_counter() - started
            status = str(_read(response, "status", "unknown"))
            if status != "completed":
                raise RuntimeError(f"Response ended with status {status}")

            raw_output = list(_read(response, "output", []))
            output_items = tuple(_dump_item(item) for item in raw_output)
            usage = _usage_from_response(_read(response, "usage", None))
            result.requests.append(
                RequestRecord(
                    request_index=request_index,
                    response_id=str(_read(response, "id", "")),
                    status=status,
                    latency_seconds=latency,
                    output_types=tuple(str(item.get("type", "unknown")) for item in output_items),
                    usage=usage,
                    output_items=output_items,
                )
            )
            input_items.extend(output_items)

            pending_calls: list[dict[str, Any]] = []
            has_message = False
            for item in output_items:
                item_type = item.get("type")
                if item_type == "function_call":
                    pending_calls.append(item)
                elif item_type == "program":
                    code = item.get("code")
                    if isinstance(code, str):
                        result.generated_programs.append(code)
                elif item_type == "program_output":
                    parsed = _parse_json_value(item.get("result"))
                    if isinstance(parsed, dict):
                        result.program_outputs.append(parsed)
                elif item_type == "message":
                    has_message = True

            if pending_calls:
                call_outputs: list[dict[str, Any]] = []
                for call in pending_calls:
                    name = str(call["name"])
                    arguments = json.loads(str(call["arguments"]))
                    tool_output = scenario.execute(name, arguments)
                    caller = call.get("caller")
                    if caller is not None and not isinstance(caller, dict):
                        caller = _dump_item(caller)
                    result.tool_calls.append(
                        ToolCallRecord(
                            request_index=request_index,
                            name=name,
                            call_id=str(call["call_id"]),
                            arguments=arguments,
                            caller=caller,
                            output=tool_output,
                        )
                    )
                    output_item: dict[str, Any] = {
                        "type": "function_call_output",
                        "call_id": call["call_id"],
                        "output": compact_json(tool_output),
                    }
                    if caller is not None:
                        output_item["caller"] = caller
                    call_outputs.append(output_item)
                input_items.extend(call_outputs)
                continue

            if has_message:
                result.final_output = str(_read(response, "output_text", ""))
                result.parsed_final_result = parse_result_json(result.final_output)
                result.total_latency_seconds = time.perf_counter() - task_started
                return result

        result.total_latency_seconds = time.perf_counter() - task_started
        raise RuntimeError(f"No final assistant message after {config.max_requests} requests")


InventoryRun = ToolCallingRun


class InventoryRunner:
    """Backward-compatible inventory wrapper around the reusable runner."""

    def __init__(self, client: ResponsesClient):
        self._runner = ToolCallingRunner(client)

    @property
    def client(self) -> ResponsesClient:
        return self._runner.client

    def run(
        self,
        *,
        arm: Arm,
        dataset: InventoryDataset,
        config: RunConfig | None = None,
        run_id: str | None = None,
    ) -> InventoryRun:
        return self._runner.run(
            arm=arm,
            scenario=dataset,
            config=config,
            run_id=run_id,
        )


def parse_result_json(text: str) -> dict[str, Any] | None:
    marker = "RESULT_JSON:"
    marker_index = text.find(marker)
    if marker_index < 0:
        return None
    tail = text[marker_index + len(marker) :].lstrip()
    try:
        value, _ = json.JSONDecoder().raw_decode(tail)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _prompt_cache_key(scenario_name: str, run_id: str, arm: Arm) -> str:
    raw_key = f"ptc-{scenario_name}:{run_id}:{arm}"
    if len(raw_key) <= 64:
        return raw_key
    digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:12]
    suffix = f":{arm}:{digest}"
    return f"{raw_key[: 64 - len(suffix)]}{suffix}"


def _usage_from_response(raw_usage: Any) -> Usage:
    if raw_usage is None:
        return Usage()
    details = _read(raw_usage, "input_tokens_details", None)
    output_details = _read(raw_usage, "output_tokens_details", None)
    return Usage(
        input_tokens=int(_read(raw_usage, "input_tokens", 0) or 0),
        cached_input_tokens=int(_read(details, "cached_tokens", 0) or 0),
        cache_write_input_tokens=int(_read(details, "cache_write_tokens", 0) or 0),
        output_tokens=int(_read(raw_usage, "output_tokens", 0) or 0),
        reasoning_output_tokens=int(_read(output_details, "reasoning_tokens", 0) or 0),
        total_tokens=int(_read(raw_usage, "total_tokens", 0) or 0),
    )


def _dump_item(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        return item
    model_dump = getattr(item, "model_dump", None)
    if callable(model_dump):
        return model_dump(exclude_none=True)
    raise TypeError(f"Cannot serialize response item of type {type(item)!r}")


def _read(value: Any, name: str, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _parse_json_value(value: Any) -> Any:
    if not isinstance(value, str):
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None
