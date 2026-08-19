from __future__ import annotations

import pytest

from ptc_benchmark.pricing import ModelPrice, PricingCatalog, estimate_usage_cost
from ptc_benchmark.runner import Usage


def test_estimated_cost_prices_each_token_class() -> None:
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


def test_estimated_cost_rejects_unknown_model() -> None:
    catalog = PricingCatalog("2026-01-01", "https://example.test", {})

    with pytest.raises(ValueError, match="No pricing snapshot"):
        estimate_usage_cost(Usage(), "missing", catalog)
