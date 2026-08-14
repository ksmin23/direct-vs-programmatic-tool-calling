# Refund Selection All-Scales Comparison

- **Source notebook:** `notebooks/03_refund_selection_and_approval.ipynb`
- **Dataset name:** `refund_selection`
- **Dataset size:** `small: 4, medium: 6, large: 8 delayed orders`
- **Case ID:** `all scales`
- **Execution date:** 2026-08-07 (Asia/Seoul)
- **Notebook cell:** 29 of 33 (code cell)
- **Section title:** `10. Optional selection scale sweep`

## Comparison results

| scale | arm | passed | requests | tool_calls | input_tokens | cached_tokens | cache_write_tokens | output_tokens | reasoning_tokens | estimated_cost_usd | end_to_end_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| small | direct | True | 3 | 17 | 3084 | 0 | 1875 | 733 | 92 | 0.039754 | 13.363 |
| small | programmatic | True | 8 | 17 | 3256 | 1266 | 1853 | 849 | 135 | 0.038369 | 17.812 |
| medium | direct | True | 3 | 25 | 3735 | 0 | 2486 | 997 | 89 | 0.051693 | 15.368 |
| medium | programmatic | True | 9 | 25 | 3321 | 1266 | 1918 | 948 | 161 | 0.041745 | 25.93 |
| large | direct | True | 3 | 33 | 4339 | 0 | 3069 | 1243 | 64 | 0.062821 | 22.62 |
| large | programmatic | True | 11 | 33 | 3330 | 1266 | 1927 | 1004 | 92 | 0.043482 | 25.338 |
