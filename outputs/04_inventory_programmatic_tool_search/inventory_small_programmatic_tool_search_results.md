# Inventory small, catalog 100 — Repeated cold/write and warm/read protocol

- Source image: `20260819_195718.jpg`
- Source notebook: `notebooks/04_inventory_programmatic_tool_search.ipynb`
- Execution cell: 8 (`repeated-comparison`)
- Dataset name: `inventory`
- Dataset size: `small`
- Case ID: `inventory-tool-search-small-100`
- Model: `gpt-5.6`
- Catalog size: `100` functions
- Repetitions per arm: `3`
- Cache phases per repetition: `cold_write`, `warm_read`
- Runs: `12` (2 arms × 3 repetitions × 2 cache phases)
- Execution date: `2026-08-14` (`Asia/Seoul`)

## Repeated cold/write and warm/read results

### `programmatic_eager`

| catalog_size | repetition | cache_phase | quality_passed | loaded_tools | input_tokens | cached_tokens | cache_write_tokens | estimated_cost_usd | end_to_end_seconds |
| ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 1 | cold_write | True | 0 | 20028 | 9779 | 9648 | 0.082354 | 13.684 |
| 100 | 1 | warm_read | True | 0 | 19985 | 19427 | 0 | 0.025014 | 12.829 |
| 100 | 2 | cold_write | True | 0 | 20028 | 9779 | 9648 | 0.082444 | 11.537 |
| 100 | 2 | warm_read | True | 0 | 20013 | 19427 | 0 | 0.025994 | 11.47 |
| 100 | 3 | cold_write | True | 0 | 20013 | 9779 | 9648 | 0.08147 | 10.312 |
| 100 | 3 | warm_read | True | 0 | 20013 | 19427 | 0 | 0.025994 | 8.858 |

### `programmatic_tool_search`

| catalog_size | repetition | cache_phase | quality_passed | loaded_tools | input_tokens | cached_tokens | cache_write_tokens | estimated_cost_usd | end_to_end_seconds |
| ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 1 | cold_write | True | 5 | 6215 | 0 | 4726 | 0.052943 | 13.42 |
| 100 | 1 | warm_read | True | 5 | 6199 | 4726 | 0 | 0.025148 | 11.464 |
| 100 | 2 | cold_write | True | 5 | 6165 | 0 | 4726 | 0.051193 | 13.096 |
| 100 | 2 | warm_read | True | 5 | 6196 | 4726 | 0 | 0.025103 | 12.915 |
| 100 | 3 | cold_write | True | 5 | 6173 | 0 | 4726 | 0.051472 | 11.278 |
| 100 | 3 | warm_read | True | 5 | 6229 | 4726 | 0 | 0.026258 | 12.887 |
