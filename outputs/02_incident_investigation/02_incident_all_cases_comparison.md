# Incident Investigation All-Cases Comparison

- **Source notebook:** `notebooks/02_incident_investigation.ipynb`
- **Dataset name:** `incident`
- **Dataset size:** `3 cases`
- **Case ID:** `all cases`
- **Execution date:** 2026-08-07 (Asia/Seoul)
- **Notebook cell:** 24 of 28 (code cell)
- **Section title:** `9. Optional three-case suite`

## Comparison results

| case_id | arm | passed | requests | tool_calls | input_tokens | cached_tokens | cache_write_tokens | output_tokens | reasoning_tokens | estimated_cost_usd | end_to_end_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| database-pool-exhaustion | direct | False | 5 | 6 | 7120 | 4406 | 1987 | 825 | 291 | 0.043007 | 22.747 |
| database-pool-exhaustion | programmatic | False | 5 | 5 | 4005 | 1475 | 2393 | 1182 | 229 | 0.051839 | 20.733 |
| expired-tls-certificate | direct | False | 5 | 4 | 5935 | 3598 | 1611 | 708 | 344 | 0.036738 | 14.072 |
| expired-tls-certificate | programmatic | False | 4 | 4 | 4417 | 1474 | 2806 | 1626 | 63 | 0.067739 | 38.865 |
| pricing-schema-mismatch | direct | False | 4 | 4 | 4750 | 2472 | 1560 | 685 | 278 | 0.035126 | 18.94 |
| pricing-schema-mismatch | programmatic | False | 3 | 3 | 4532 | 1469 | 2926 | 1716 | 257 | 0.071187 | 27.849 |
