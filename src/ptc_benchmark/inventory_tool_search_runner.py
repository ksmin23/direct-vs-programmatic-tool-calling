from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol

from .inventory import compact_json
from .inventory_tool_search import InventoryToolSearchArm, InventoryToolSearchScenario
from .runner import RequestRecord, Usage, parse_result_json


class ResponsesClient(Protocol):
    responses: Any


@dataclass(frozen=True)
class ToolSearchRunConfig:
    model: str = "gpt-5.6"
    reasoning_effort: str = "low"
    max_output_tokens: int = 8_192
    max_requests: int = 16
    store: bool = False


@dataclass(frozen=True)
class ToolSearchEvent:
    sequence: int
    request_index: int
    position: int
    type: str
    detail: str = ""


@dataclass(frozen=True)
class NamespacedToolCallRecord:
    request_index: int
    namespace: str
    name: str
    call_id: str
    arguments: dict[str, Any]
    caller: dict[str, Any] | None
    output: dict[str, Any]

    @property
    def qualified_name(self) -> str:
        return f"{self.namespace}.{self.name}" if self.namespace else self.name


@dataclass
class InventoryToolSearchRun:
    arm: InventoryToolSearchArm
    experiment_id: str
    repetition: int
    model: str
    scenario: str
    case_id: str
    catalog_size: int
    prompt_cache_key: str
    requests: list[RequestRecord] = field(default_factory=list)
    events: list[ToolSearchEvent] = field(default_factory=list)
    loaded_tools: set[str] = field(default_factory=set)
    tool_calls: list[NamespacedToolCallRecord] = field(default_factory=list)
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
        value = asdict(self)
        value["loaded_tools"] = sorted(self.loaded_tools)
        return value


class InventoryToolSearchRunner:
    def __init__(self, client: ResponsesClient):
        self.client = client

    def run(
        self,
        *,
        arm: InventoryToolSearchArm,
        scenario: InventoryToolSearchScenario,
        config: ToolSearchRunConfig | None = None,
        experiment_id: str = "inventory-tool-search",
        repetition: int = 1,
    ) -> InventoryToolSearchRun:
        config = config or ToolSearchRunConfig()
        instructions, user_input = scenario.prompt(arm)
        cache_key = build_tool_search_cache_key(
            experiment_id=experiment_id,
            catalog_size=scenario.catalog_size,
            arm=arm,
            repetition=repetition,
        )
        input_items: list[dict[str, Any]] = [
            {
                "role": "developer",
                "content": [
                    {
                        "type": "input_text",
                        "text": instructions,
                        "prompt_cache_breakpoint": {"mode": "explicit"},
                    }
                ],
            },
            {"role": "user", "content": [{"type": "input_text", "text": user_input}]},
        ]
        tools = scenario.tool_definitions(arm)
        result = InventoryToolSearchRun(
            arm=arm,
            experiment_id=experiment_id,
            repetition=repetition,
            model=config.model,
            scenario=scenario.scenario_name,
            case_id=scenario.case_id,
            catalog_size=scenario.catalog_size,
            prompt_cache_key=cache_key,
        )
        task_started = time.perf_counter()

        for request_index in range(config.max_requests):
            request: dict[str, Any] = {
                "model": config.model,
                "input": input_items,
                "tools": tools,
                "store": config.store,
                "parallel_tool_calls": True,
                "reasoning": {"effort": config.reasoning_effort},
                "max_output_tokens": config.max_output_tokens,
                "prompt_cache_key": cache_key,
                "prompt_cache_options": {"mode": "explicit"},
            }
            if arm == "programmatic_eager" and request_index == 0:
                request["tool_choice"] = {"type": "programmatic_tool_calling"}

            started = time.perf_counter()
            response = self.client.responses.create(**request)
            latency = time.perf_counter() - started
            status = str(_read(response, "status", "unknown"))
            if status != "completed":
                raise RuntimeError(f"Response ended with status {status}")

            raw_output = list(_read(response, "output", []))
            output_items = tuple(_dump_item(item) for item in raw_output)
            result.requests.append(
                RequestRecord(
                    request_index=request_index,
                    response_id=str(_read(response, "id", "")),
                    status=status,
                    latency_seconds=latency,
                    output_types=tuple(str(item.get("type", "unknown")) for item in output_items),
                    usage=_usage_from_response(_read(response, "usage", None)),
                    output_items=output_items,
                )
            )
            input_items.extend(output_items)

            pending_calls: list[dict[str, Any]] = []
            has_message = False
            for position, item in enumerate(output_items):
                item_type = str(item.get("type", "unknown"))
                detail = _event_detail(item)
                result.events.append(
                    ToolSearchEvent(
                        sequence=len(result.events) + 1,
                        request_index=request_index,
                        position=position,
                        type=item_type,
                        detail=detail,
                    )
                )
                if item_type == "tool_search_output":
                    result.loaded_tools.update(_loaded_tool_names(item))
                elif item_type == "function_call":
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
                    namespace = str(call.get("namespace") or "inventory")
                    name = str(call["name"])
                    arguments = _parse_arguments(call.get("arguments"))
                    tool_output = scenario.execute(namespace, name, arguments)
                    caller = call.get("caller")
                    if caller is not None and not isinstance(caller, dict):
                        caller = _dump_item(caller)
                    result.tool_calls.append(
                        NamespacedToolCallRecord(
                            request_index=request_index,
                            namespace=namespace,
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


def build_tool_search_cache_key(
    *,
    experiment_id: str,
    catalog_size: int,
    arm: InventoryToolSearchArm,
    repetition: int,
) -> str:
    raw = f"ptc-ts:{experiment_id}:{catalog_size}:{arm}:r{repetition}"
    if len(raw) <= 64:
        return raw
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"{raw[:51]}:{digest}"


def comparison_order(repetition: int) -> tuple[InventoryToolSearchArm, InventoryToolSearchArm]:
    if repetition < 1:
        raise ValueError("repetition must be at least 1")
    if repetition % 2:
        return "programmatic_eager", "programmatic_tool_search"
    return "programmatic_tool_search", "programmatic_eager"


def semantic_timeline(run: InventoryToolSearchRun) -> list[dict[str, Any]]:
    return [
        {
            "sequence": event.sequence,
            "request": event.request_index + 1,
            "type": event.type,
            "detail": event.detail,
        }
        for event in run.events
    ]


def _event_detail(item: dict[str, Any]) -> str:
    item_type = item.get("type")
    if item_type == "tool_search_call":
        return json.dumps(item.get("arguments", {}), ensure_ascii=False, sort_keys=True)
    if item_type == "tool_search_output":
        return ", ".join(_loaded_tool_names(item)) or "(no tools loaded)"
    if item_type == "function_call":
        namespace = item.get("namespace") or "inventory"
        return f"{namespace}.{item.get('name', 'unknown')}"
    if item_type == "program":
        return "generated JavaScript"
    if item_type == "program_output":
        return "structured program result"
    if item_type == "message":
        return "final assistant message"
    return ""


def _loaded_tool_names(item: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for tool in item.get("tools", []):
        if tool.get("type") == "namespace":
            namespace = str(tool.get("name", "unknown"))
            names.extend(
                f"{namespace}.{function.get('name', 'unknown')}"
                for function in tool.get("tools", [])
            )
        elif tool.get("name"):
            names.append(str(tool["name"]))
    return names


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


def _parse_arguments(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("Function-call arguments must be a JSON object")


def _parse_json_value(value: Any) -> Any:
    if not isinstance(value, str):
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


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
