from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Protocol

from .pricing import CostEstimate
from .runner import ToolCallingRun


class EvaluationResult(Protocol):
    passed: bool


def comparison_rows(
    results: Iterable[tuple[ToolCallingRun, EvaluationResult, CostEstimate]],
) -> list[dict[str, object]]:
    rows = []
    for run, evaluation, cost in results:
        usage = run.usage
        rows.append(
            {
                "arm": run.arm,
                "passed": evaluation.passed,
                "requests": len(run.requests),
                "tool_calls": len(run.tool_calls),
                "input_tokens": usage.input_tokens,
                "cached_tokens": usage.cached_input_tokens,
                "cache_write_tokens": usage.cache_write_input_tokens,
                "output_tokens": usage.output_tokens,
                "reasoning_tokens": usage.reasoning_output_tokens,
                "estimated_cost_usd": round(cost.total_cost, 6),
                "end_to_end_seconds": round(run.total_latency_seconds, 3),
            }
        )
    return rows


def request_timeline(run: ToolCallingRun) -> list[dict[str, object]]:
    return [
        {
            "request": record.request_index + 1,
            "output_types": ", ".join(record.output_types),
            "input_tokens": record.usage.input_tokens,
            "cached_tokens": record.usage.cached_input_tokens,
            "cache_write_tokens": record.usage.cache_write_input_tokens,
            "output_tokens": record.usage.output_tokens,
            "latency_seconds": round(record.latency_seconds, 3),
        }
        for record in run.requests
    ]


def markdown_table(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "_No rows._"
    headers = list(rows[0])
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row[header]) for header in headers) + " |")
    return "\n".join(lines)


def append_jsonl(
    path: str | Path,
    run: ToolCallingRun,
    evaluation: EvaluationResult,
    cost: CostEstimate,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "run": run.to_dict(),
        "evaluation": asdict(evaluation),
        "cost": asdict(cost),
    }
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
