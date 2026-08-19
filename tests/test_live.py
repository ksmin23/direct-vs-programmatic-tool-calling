from __future__ import annotations

import os

import pytest

from ptc_benchmark.inventory import build_inventory_dataset
from ptc_benchmark.runner import InventoryRunner, RunConfig


pytestmark = pytest.mark.live


def _live_enabled() -> bool:
    return os.getenv("RUN_LIVE_SMOKE") == "1" and bool(os.getenv("OPENAI_API_KEY"))


@pytest.mark.skipif(not _live_enabled(), reason="set RUN_LIVE_SMOKE=1 and OPENAI_API_KEY")
@pytest.mark.parametrize("arm", ["direct", "programmatic"])
def test_live_small_inventory_response_completes(arm: str) -> None:
    from openai import OpenAI

    run = InventoryRunner(OpenAI()).run(
        arm=arm,
        dataset=build_inventory_dataset("small"),
        config=RunConfig(model=os.getenv("OPENAI_MODEL", "gpt-5.6"), max_requests=16),
        run_id=f"live-smoke-{arm}",
    )

    assert run.final_output
    assert run.parsed_final_result is not None
