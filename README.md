# Direct vs. Programmatic Tool Calling

This notebook-first benchmark compares
[Direct Tool Calling](https://developers.openai.com/api/docs/guides/function-calling),
[Programmatic Tool Calling](https://developers.openai.com/api/docs/guides/tools-programmatic-tool-calling),
and Programmatic Tool Calling combined with
[hosted Tool Search](https://developers.openai.com/api/docs/guides/tools-tool-search).

The project uses deterministic workflows, explicit quality gates, versioned pricing,
and saved execution artifacts to examine more than token count alone. Each comparison
also records request structure, tool-call linkage, intermediate payloads, cache usage,
estimated cost, and end-to-end latency.

## Implemented scenarios

### 1. Inventory tool-call trace

[`00_inventory_tool_call_trace.ipynb`](notebooks/00_inventory_tool_call_trace.ipynb)
shows how the same fixed-fan-out inventory task appears under Direct and Programmatic
Tool Calling. The normalized semantic timeline makes the observable request lifecycle,
function calls, generated program, caller linkage, and final response easy to compare.

OpenAI Trace export is optional and sends bounded event summaries. Full deterministic
payloads can remain in the local timeline. Trace output shows observable execution
events; it does not expose hidden chain-of-thought reasoning.

Saved results:

- [Small live comparison](outputs/00_inventory_tool_call_trace/inventory_small_live_comparison_trace_export.md)
- [Small normalized timeline](outputs/00_inventory_tool_call_trace/inventory_small_normalized_semantic_timeline.md)
- [Medium live comparison](outputs/00_inventory_tool_call_trace/inventory_medium_live_comparison_trace_export.md)
- [Medium normalized timeline](outputs/00_inventory_tool_call_trace/inventory_medium_normalized_semantic_timeline.md)

### 2. Inventory replenishment

[`01_inventory_replenishment.ipynb`](notebooks/01_inventory_replenishment.ipynb)
compares Direct and Programmatic Tool Calling on a fixed fan-out task. Both arms use
the same model, reasoning effort, SKU fixtures, task contract, and three read-only
function tools.

Direct Tool Calling may emit independent calls in parallel. The Programmatic arm must
coordinate the calls from generated JavaScript and reduce the detailed intermediate
data before returning a result. A run must pass all quality checks before its cost is
compared:

- call all three tools exactly once for every SKU;
- produce the exact structured replenishment plan;
- preserve program caller linkage in the Programmatic arm;
- return the expected `RESULT_JSON`; and
- explain every recommendation with its source and calculated unit values.

Saved results: [Inventory replenishment outputs](outputs/01_inventory_replenishment/)

### 3. Incident investigation

[`02_incident_investigation.ipynb`](notebooks/02_incident_investigation.ipynb)
tests an adaptive workflow. Both arms start with the same checkout log search and
error-rate metric, then use the evidence semantics to choose a trace,
dependent-service metric, or recent deployment lookup. The deterministic suite covers
database pool exhaustion, an expired TLS certificate, and a pricing schema mismatch.

The quality gate requires the exact root cause and remediation, a grounded and
evidence-complete explanation, the required two-call start, no duplicate calls, and
correct caller linkage. This scenario highlights the tradeoff between processing
intermediate evidence inside generated JavaScript and allowing the model to make
semantic decisions between Direct calls.

Saved results: [Incident investigation outputs](outputs/02_incident_investigation/)

### 4. Refund selection and approval

[`03_refund_selection_and_approval.ipynb`](notebooks/03_refund_selection_and_approval.ipynb)
separates bulk read processing from sensitive actions. Candidate selection compares
Direct with Programmatic across delayed-order, delivery, refund-history, and policy
records. The end-to-end comparison is All-Direct versus Hybrid: Hybrid uses
Programmatic Tool Calling for selection and a separate Direct stage for approval
requests and simulated refund issuance.

Approval and refund tools declare `allowed_callers=["direct"]` and are never exposed
to generated programs. An invalid or ungrounded selection stops the workflow before
the action stage. All actions are deterministic local simulations; no real refund
system is connected.

Saved results:
[Refund selection and approval outputs](outputs/03_refund_selection_and_approval/)

### 5. Programmatic Tool Calling with and without Tool Search

[`04_inventory_programmatic_tool_search.ipynb`](notebooks/04_inventory_programmatic_tool_search.ipynb)
uses inventory replenishment as the scenario for a different primary comparison:

- `programmatic_eager` exposes every function schema up front.
- `programmatic_tool_search` marks schemas with `defer_loading: true`, uses hosted
  Tool Search at the top level, and lets the generated program call only definitions
  loaded with `allowed_callers=["programmatic"]`.
- `direct_eager` is available only as an optional reference arm.

The catalog can contain 20, 50, 100, or 200 functions. The quality gate verifies the
Tool Search → program → function call → program output → final message sequence,
required inventory tools, absence of unrelated namespaces, exact SKU/tool execution
coverage, caller linkage, program output, and final response. Loading an extra helper
from the inventory namespace is an efficiency warning; loading another namespace is
a failure.

The repeated protocol uses isolated explicit cache keys and pairs each cold/write run
with a warm/read run. In the saved 100-function experiments, Tool Search reduced input
tokens by about 69% for both dataset sizes while preserving quality. Its largest cost
advantage occurred during cold cache writes. Latency increased for the small workload
but decreased for the medium workload, so the result is treated as directional rather
than a universal latency claim.

Saved results:

- [Small repeated cold/write and warm/read results](outputs/04_inventory_programmatic_tool_search/inventory_small_programmatic_tool_search_results.md)
- [Medium repeated cold/write and warm/read results](outputs/04_inventory_programmatic_tool_search/inventory_medium_programmatic_tool_search_results.md)
- [Small and medium comparative analysis](outputs/04_inventory_programmatic_tool_search/inventory_programmatic_tool_search_comparison_analysis.md)

## What the benchmark records

Depending on the scenario, the notebooks and runners record:

- model requests and host round trips;
- function calls, arguments, results, and caller linkage;
- generated JavaScript programs and program outputs;
- normalized semantic timelines;
- input, cached-input, cache-write, output, and reasoning tokens;
- locally serialized intermediate payload size;
- request and end-to-end latency;
- estimated cost from a dated pricing snapshot; and
- deterministic quality-gate results.

`intermediate_payload_bytes` is a local serialization measurement, not a billable API
token count. Estimated cost separates uncached input, cache-read input, cache-write
input, and output tokens before applying the versioned model prices.

## Project layout

```text
notebooks/
  00_inventory_tool_call_trace.ipynb          # Direct vs. Programmatic trace lifecycle
  01_inventory_replenishment.ipynb            # fixed-fan-out inventory benchmark
  02_incident_investigation.ipynb             # adaptive investigation benchmark
  03_refund_selection_and_approval.ipynb      # read/action safety boundary
  04_inventory_programmatic_tool_search.ipynb # Tool Search vs. eager tool loading
outputs/                                      # checked-in Markdown experiment evidence
pricing/                                      # dated, replaceable pricing snapshots
src/ptc_benchmark/                            # scenarios, runners, evaluation, pricing
src/ptc_trace_demo/                           # bounded OpenAI Trace integration
tests/                                        # offline, notebook, mocked runner, and opt-in live tests
pyproject.toml                                # package and dependency-group configuration
requirements.txt                             # pip-compatible minimum dependencies
```

## Setup

Python 3.11 or newer is required. Use either `uv` or a standard virtual environment
with `pip`.

### Using `uv`

```bash
cd direct-vs-programmatic-tool-calling
uv sync --group dev
cp .env.local.example .env.local
```

### Using `pip`

`requirements.txt` contains minimum versions for the runtime, notebook, test, and
Trace-export dependencies.

```bash
cd direct-vs-programmatic-tool-calling
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.local.example .env.local
```

Add `OPENAI_API_KEY` to `.env.local` only when intentionally running live API calls.
Never commit that file.

## Run the notebooks

```bash
uv run jupyter lab notebooks/00_inventory_tool_call_trace.ipynb
uv run jupyter lab notebooks/01_inventory_replenishment.ipynb
uv run jupyter lab notebooks/02_incident_investigation.ipynb
uv run jupyter lab notebooks/03_refund_selection_and_approval.ipynb
uv run jupyter lab notebooks/04_inventory_programmatic_tool_search.ipynb
```

The notebooks use explicit `RUN_*` controls for API calls and larger experiment
sweeps. Some notebooks may be saved with live controls enabled to preserve the exact
state of a recorded experiment. Before using **Run All**, inspect the controls cell
and set every live flag to `False` unless you intentionally want API calls that may
incur cost.

Key controls:

- `RUN_LIVE`: enables API-backed execution.
- `RUN_REPEATED_COMPARISON`: enables repeated comparisons after `RUN_LIVE`.
- `RUN_ALL_CASES`: runs the complete incident suite.
- `RUN_APPROVAL_WORKFLOW`: enables the deterministic simulated refund action stage.
- `RUN_ALL_SCALES`: enables the configured scale or catalog sweep.
- `INCLUDE_DIRECT_BASELINE`: adds the optional Direct reference to the Tool Search
  notebook.

The `00_` Trace notebook also provides:

- `EXPORT_OPENAI_TRACE`: exports bounded event summaries and requires `RUN_LIVE`.
- `SHOW_TRACE_ERROR_DETAILS`: temporarily includes Trace ingest response details in
  SDK error logs. Keep it disabled during normal use because logs may contain model
  or tool data.
- `INCLUDE_LOCAL_PAYLOADS`: retains complete deterministic payloads in the local
  normalized timeline only.

The `04_` Tool Search notebook uses an explicit prompt-cache breakpoint and isolated
keys for each arm, catalog size, and repetition. `CATALOG_SIZE`, `DATASET_SCALE`, and
`REPETITIONS` control the selected experiment.

## Verify without API cost

```bash
uv run pytest -m "not live"
```

With the `pip` setup:

```bash
PYTHONPATH=src python -m pytest -m "not live"
```

The offline suite validates deterministic inventory, incident, refund, Tool Search,
pricing, Trace, and mocked Responses runner behavior. It also executes in-memory copies
of every notebook after forcing all live controls to `False`; the committed notebooks
and their saved outputs are not modified.

### Test layout

- `test_inventory.py` and `test_inventory_runner.py`: inventory fixtures, oracle,
  result parsing, and function-call continuation.
- `test_incident.py` and `test_incident_runner.py`: incident fixtures, grounded
  expected results, and runner request metadata.
- `test_inventory_tool_search.py` and `test_inventory_tool_search_runner.py`: catalog
  construction, deferred definitions, explicit cache boundaries, loaded tools, and
  comparison ordering.
- `test_refund.py` and `test_refund_runner.py`: refund selection fixtures, Direct-only
  action tools, and workflow termination before unsafe actions.
- `test_inventory_trace.py`: normalized trace timelines and default log redaction.
- `test_pricing.py`: token-class pricing and missing-model errors.
- `test_notebook.py`: offline execution and live-control isolation for every notebook.
- `test_live.py`: opt-in Direct and Programmatic small-inventory API smoke tests.

## Opt-in live runs

The live marker contains a small inventory smoke test for both Direct and Programmatic
Tool Calling. It remains skipped unless both `RUN_LIVE_SMOKE=1` and `OPENAI_API_KEY`
are present, and it may incur API charges.

```bash
RUN_LIVE_SMOKE=1 uv run --env-file .env.local pytest -m live -s
```

For scenario-scale live comparisons, open the relevant notebook, review its scale,
model, reasoning, and repetition settings, then explicitly enable only the required
`RUN_*` controls.

`OPENAI_MODEL` defaults to `gpt-5.6`. Both arms use the same model and reasoning effort
within a comparison. `OPENAI_PRICING_PATH` can override the checked-in pricing snapshot
used for cost estimates.

## Interpretation limits

- Programmatic Tool Calling is not expected to outperform Direct Tool Calling for
  every task or scale.
- A lower token count or estimated cost is not a win when the quality gate fails.
- Context efficiency, billed cost, and latency are separate outcomes.
- Bulk-read efficiency does not justify exposing approval or write tools to generated
  code.
- Local tools are deterministic and have no network latency, so measured latency is
  dominated by API requests, model behavior, and hosted-tool scheduling.
- Saved experiments use small sample sizes and should not be treated as production
  latency benchmarks.
- Pricing changes over time. Update or override the dated snapshot before relying on
  the estimates.
- The current calculator excludes the GPT-5.6 long-context surcharge because these
  experiments remain far below 272K input tokens.

## Official references

- [Function calling](https://developers.openai.com/api/docs/guides/function-calling)
- [Programmatic Tool Calling](https://developers.openai.com/api/docs/guides/tools-programmatic-tool-calling)
- [Tool Search](https://developers.openai.com/api/docs/guides/tools-tool-search)
- [GPT-5.6 model comparison and pricing](https://developers.openai.com/api/docs/models/compare)
