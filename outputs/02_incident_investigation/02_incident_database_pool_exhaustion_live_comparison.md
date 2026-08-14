# Incident Database Pool Exhaustion Live Direct vs Programmatic Comparison

- **Source notebook:** `notebooks/02_incident_investigation.ipynb`
- **Dataset name:** `incident`
- **Dataset size:** `single case`
- **Case ID:** `database-pool-exhaustion`
- **Execution date:** 2026-08-07 (Asia/Seoul)
- **Notebook cell:** 19 of 28 (code cell)
- **Section title:** `7. Optional single-case live comparison`

## Comparison results

| arm | passed | requests | tool_calls | input_tokens | cached_tokens | cache_write_tokens | output_tokens | reasoning_tokens | estimated_cost_usd | end_to_end_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| direct | False | 4 | 5 | 5149 | 2602 | 1823 | 818 | 334 | 0.040855 | 23.429 |
| programmatic | False | 6 | 6 | 4968 | 1475 | 3356 | 2116 | 535 | 0.085877 | 37.886 |

## Quality gate failures

- **Direct:**
  - The structured execution result does not match the incident oracle.
  - `RESULT_JSON` does not match the incident oracle.
- **Programmatic:**
  - The structured execution result does not match the incident oracle.
  - `RESULT_JSON` does not match the incident oracle.
  - `EXPLANATION` omits the diagnosis, action, service, or required evidence IDs.
