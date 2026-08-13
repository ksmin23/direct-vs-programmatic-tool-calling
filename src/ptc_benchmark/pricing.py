from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .runner import ToolCallingRun, Usage


@dataclass(frozen=True)
class ModelPrice:
    input_per_million: float
    cached_input_per_million: float
    cache_write_input_per_million: float
    output_per_million: float


@dataclass(frozen=True)
class PricingCatalog:
    effective_date: str
    source_url: str
    models: dict[str, ModelPrice]


@dataclass(frozen=True)
class CostEstimate:
    uncached_input_tokens: int
    cached_input_tokens: int
    cache_write_input_tokens: int
    output_tokens: int
    uncached_input_cost: float
    cached_input_cost: float
    cache_write_input_cost: float
    output_cost: float
    total_cost: float
    pricing_effective_date: str
    pricing_source_url: str


def load_pricing_catalog(path: str | Path) -> PricingCatalog:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    models = {
        model: ModelPrice(**values)
        for model, values in payload["models"].items()
    }
    return PricingCatalog(
        effective_date=payload["effective_date"],
        source_url=payload["source_url"],
        models=models,
    )


def estimate_run_cost(run: ToolCallingRun, catalog: PricingCatalog) -> CostEstimate:
    return estimate_usage_cost(run.usage, run.model, catalog)


def estimate_usage_cost(usage: Usage, model: str, catalog: PricingCatalog) -> CostEstimate:
    try:
        price = catalog.models[model]
    except KeyError as exc:
        raise ValueError(
            f"No pricing snapshot for {model!r}. Add it to the catalog or override OPENAI_MODEL."
        ) from exc
    cached = usage.cached_input_tokens
    cache_write = usage.cache_write_input_tokens
    uncached = max(usage.input_tokens - cached - cache_write, 0)
    divisor = 1_000_000
    uncached_cost = uncached * price.input_per_million / divisor
    cached_cost = cached * price.cached_input_per_million / divisor
    cache_write_cost = cache_write * price.cache_write_input_per_million / divisor
    output_cost = usage.output_tokens * price.output_per_million / divisor
    return CostEstimate(
        uncached_input_tokens=uncached,
        cached_input_tokens=cached,
        cache_write_input_tokens=cache_write,
        output_tokens=usage.output_tokens,
        uncached_input_cost=uncached_cost,
        cached_input_cost=cached_cost,
        cache_write_input_cost=cache_write_cost,
        output_cost=output_cost,
        total_cost=uncached_cost + cached_cost + cache_write_cost + output_cost,
        pricing_effective_date=catalog.effective_date,
        pricing_source_url=catalog.source_url,
    )
