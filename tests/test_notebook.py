from __future__ import annotations

import re
from pathlib import Path

import nbformat
import pytest
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = tuple(sorted((ROOT / "notebooks").glob("*.ipynb")))
LIVE_ASSIGNMENT = re.compile(
    r"^(RUN_LIVE|RUN_REPEATED_COMPARISON|RUN_ALL_CASES|RUN_APPROVAL_WORKFLOW|"
    r"RUN_ALL_SCALES|INCLUDE_DIRECT_BASELINE|EXPORT_OPENAI_TRACE)\s*=.*$",
    re.MULTILINE,
)


def _offline_copy(path: Path):
    notebook = nbformat.read(path, as_version=4)
    for cell in notebook.cells:
        if cell.cell_type == "code":
            cell.source = LIVE_ASSIGNMENT.sub(r"\1 = False", cell.source)
    return notebook


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda path: path.name)
def test_notebook_executes_offline(path: Path) -> None:
    notebook = _offline_copy(path)

    NotebookClient(
        notebook,
        timeout=120,
        kernel_name="python3",
        resources={"metadata": {"path": str(ROOT)}},
    ).execute()


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda path: path.name)
def test_offline_copy_disables_every_live_control(path: Path) -> None:
    notebook = _offline_copy(path)
    source = "\n".join(
        cell.source for cell in notebook.cells if cell.cell_type == "code"
    )

    assert not re.search(r"^RUN_[A-Z_]+\s*=\s*True", source, re.MULTILINE)
    assert not re.search(r"^EXPORT_OPENAI_TRACE\s*=\s*True", source, re.MULTILINE)
