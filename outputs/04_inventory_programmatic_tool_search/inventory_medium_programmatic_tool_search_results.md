# Inventory medium, catalog 100 — Repeated cold/write and warm/read protocol

- Source image: `20260819_195846.jpg`
- Source notebook: `notebooks/04_inventory_programmatic_tool_search.ipynb`
- Execution cell: 8 (`repeated-comparison`)
- Dataset name: `inventory`
- Dataset size: `medium`
- Case ID: `inventory-tool-search-medium-100`
- SKU count: `10`
- Required tool calls per run: `30` (10 SKUs × 3 tools)
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
| 100 | 1 | cold_write | True | 0 | 20179 | 9807 | 9676 | 0.087848 | 18.655 |
| 100 | 1 | warm_read | True | 0 | 20183 | 19483 | 0 | 0.032382 | 20.171 |
| 100 | 2 | cold_write | True | 0 | 20157 | 9807 | 9676 | 0.086719 | 15.169 |
| 100 | 2 | warm_read | True | 0 | 20168 | 19483 | 0 | 0.031467 | 13.781 |
| 100 | 3 | cold_write | True | 0 | 20220 | 9807 | 9676 | 0.089403 | 16.302 |
| 100 | 3 | warm_read | True | 0 | 20206 | 19483 | 0 | 0.033277 | 15.891 |

### `programmatic_tool_search`

| catalog_size | repetition | cache_phase | quality_passed | loaded_tools | input_tokens | cached_tokens | cache_write_tokens | estimated_cost_usd | end_to_end_seconds |
| ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 1 | cold_write | True | 5 | 6375 | 0 | 4782 | 0.059393 | 15.867 |
| 100 | 1 | warm_read | True | 5 | 6366 | 4782 | 0 | 0.031071 | 15.915 |
| 100 | 2 | cold_write | True | 5 | 6320 | 0 | 4782 | 0.056958 | 13.878 |
| 100 | 2 | warm_read | True | 5 | 6408 | 4782 | 0 | 0.032571 | 15.451 |
| 100 | 3 | cold_write | True | 5 | 6356 | 0 | 4782 | 0.058217 | 11.904 |
| 100 | 3 | warm_read | True | 5 | 6317 | 4782 | 0 | 0.029356 | 15.265 |
