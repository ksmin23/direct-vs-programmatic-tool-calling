# Refund Small Selection Live Direct vs Programmatic Comparison

- **Source notebook:** `notebooks/03_refund_selection_and_approval.ipynb`
- **Dataset name:** `refund_selection`
- **Dataset size:** `small (4 delayed orders)`
- **Case ID:** `refund-small`
- **Execution date:** 2026-08-07 (Asia/Seoul)
- **Notebook cell:** 21 of 33 (code cell)
- **Section title:** `7. Optional read-only selection comparison`

## Comparison results

| arm | passed | requests | tool_calls | input_tokens | cached_tokens | cache_write_tokens | output_tokens | reasoning_tokens | estimated_cost_usd | end_to_end_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| direct | True | 3 | 17 | 3083 | 0 | 1875 | 733 | 92 | 0.039749 | 13.842 |
| programmatic | True | 8 | 17 | 3410 | 1266 | 2007 | 997 | 113 | 0.043772 | 24.332 |
