# Inventory medium — Normalized semantic timeline

- Source notebook: `notebooks/00_inventory_tool_call_trace.ipynb`
- Execution cell: 16 (`timeline`)
- Dataset name: `inventory`
- Dataset size: `medium`
- Case ID: `inventory-medium`
- SKU count: 10
- Execution date: `2026-08-07` (`Asia/Seoul`)

## output 1

### Direct timeline

| sequence | arm | elapsed_ms | duration_ms | event | name | request | call_id | caller_id | payload_bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | direct | 7907.2 | 7906.4 | model_request | request_1 | 1 | None | None | 11890 |
| 2 | direct | 7907.3 | 0.0 | function_call | get_inventory | 1 | call_bLqgcyJFhamdUP3gaSN17MGD | None | 207 |
| 3 | direct | 7907.3 | 0.0 | function_call | get_weekly_demand | 1 | call_ME1oaz1S49CFuo8DjfUzGJBc | None | 211 |
| 4 | direct | 7907.4 | 0.0 | function_call | get_inbound_shipments | 1 | call_z0ZQsQC8otyDvYpnmwuB0phT | None | 215 |
| 5 | direct | 7907.4 | 0.0 | function_call | get_inventory | 1 | call_qvCg85pnTruLgZwsFdBgL5if | None | 207 |
| 6 | direct | 7907.4 | 0.0 | function_call | get_weekly_demand | 1 | call_Bpl3EJRI5kV4BvLa5uowKFLB | None | 211 |
| 7 | direct | 7907.5 | 0.0 | function_call | get_inbound_shipments | 1 | call_xluuTymePku2100nypzFiqeu | None | 215 |
| 8 | direct | 7907.5 | 0.0 | function_call | get_inventory | 1 | call_HpywyGJNz4og1eufXKZOI9p4 | None | 207 |
| 9 | direct | 7907.5 | 0.0 | function_call | get_weekly_demand | 1 | call_4ZpceCYx3nG5Hrogu04mNSEw | None | 211 |
| 10 | direct | 7907.6 | 0.0 | function_call | get_inbound_shipments | 1 | call_000qE8knp61WSDEIRyGz5sWm | None | 215 |
| 11 | direct | 7907.6 | 0.0 | function_call | get_inventory | 1 | call_1IMXBBwrBqSR70SkX2ZIDS7w | None | 207 |
| 12 | direct | 7907.6 | 0.0 | function_call | get_weekly_demand | 1 | call_K4jj4GebFC0QWQ52bTYcJ9V5 | None | 211 |
| 13 | direct | 7907.7 | 0.0 | function_call | get_inbound_shipments | 1 | call_lEhAKJUVz2DdT7MiUnlM9Un6 | None | 215 |
| 14 | direct | 7907.7 | 0.0 | function_call | get_inventory | 1 | call_ubdiaVQ2wjcBr602G6jmSvsy | None | 207 |
| 15 | direct | 7907.7 | 0.0 | function_call | get_weekly_demand | 1 | call_D3CuBUYsgGqJYQso8CPejmL1 | None | 211 |
| 16 | direct | 7907.8 | 0.0 | function_call | get_inbound_shipments | 1 | call_FwmHX9APLCRiuqKYvgodahXT | None | 215 |
| 17 | direct | 7907.8 | 0.0 | function_call | get_inventory | 1 | call_pC0chqEsmEN0k2fjizwJVm4L | None | 207 |
| 18 | direct | 7907.8 | 0.0 | function_call | get_weekly_demand | 1 | call_PRWmEnRBD1BsSq8hbKuVJj4s | None | 211 |
| 19 | direct | 7907.9 | 0.0 | function_call | get_inbound_shipments | 1 | call_bl2dKOM0nrF4n58bqUT4o08s | None | 215 |
| 20 | direct | 7907.9 | 0.0 | function_call | get_inventory | 1 | call_by5BecRha4P3kJt0rE39bGGN | None | 207 |
| 21 | direct | 7907.9 | 0.0 | function_call | get_weekly_demand | 1 | call_wsz43h13yR6R8APNdF8xkfBN | None | 211 |
| 22 | direct | 7907.9 | 0.0 | function_call | get_inbound_shipments | 1 | call_lkHANlH9U95k3fUoHGUtID3b | None | 215 |
| 23 | direct | 7908.0 | 0.0 | function_call | get_inventory | 1 | call_Hi3Z1vdKQmrKKB2bGDwwSqMb | None | 207 |
| 24 | direct | 7908.0 | 0.0 | function_call | get_weekly_demand | 1 | call_YV7mX5njYuZRA2V2TK2TAfj6 | None | 211 |
| 25 | direct | 7908.0 | 0.0 | function_call | get_inbound_shipments | 1 | call_tgs8GYcshE7CEMNLBudy0kYw | None | 215 |
| 26 | direct | 7908.1 | 0.0 | function_call | get_inventory | 1 | call_XNZ5Ti340pXrTxt6RbGkMt8b | None | 207 |
| 27 | direct | 7908.1 | 0.0 | function_call | get_weekly_demand | 1 | call_kfHgcTNw52FgooSLehk3zKid | None | 211 |
| 28 | direct | 7908.1 | 0.0 | function_call | get_inbound_shipments | 1 | call_pTiZZjeeNTU2fBr0Czw9w1M6 | None | 215 |
| 29 | direct | 7908.2 | 0.0 | function_call | get_inventory | 1 | call_rRwJpnjhVoTJoJ9qRnyoqVkM | None | 207 |
| 30 | direct | 7908.2 | 0.0 | function_call | get_weekly_demand | 1 | call_3KyuzI3aHdUKCatAvKD8SLSC | None | 211 |
| 31 | direct | 7908.2 | 0.0 | function_call | get_inbound_shipments | 1 | call_a4kZKb5z2FbGHgpRbEhvWVf9 | None | 215 |
| 32 | direct | 7908.7 | 0.3 | tool_output | get_inventory | 1 | call_bLqgcyJFhamdUP3gaSN17MGD | None | 312 |
| 33 | direct | 7908.8 | 0.0 | tool_output | get_weekly_demand | 1 | call_ME1oaz1S49CFuo8DjfUzGJBc | None | 357 |
| 34 | direct | 7908.9 | 0.0 | tool_output | get_inbound_shipments | 1 | call_z0ZQsQC8otyDvYpnmwuB0phT | None | 376 |
| 35 | direct | 7909.0 | 0.1 | tool_output | get_inventory | 1 | call_qvCg85pnTruLgZwsFdBgL5if | None | 313 |
| 36 | direct | 7909.1 | 0.1 | tool_output | get_weekly_demand | 1 | call_Bpl3EJRI5kV4BvLa5uowKFLB | None | 357 |
| 37 | direct | 7909.2 | 0.1 | tool_output | get_inbound_shipments | 1 | call_xluuTymePku2100nypzFiqeu | None | 378 |
| 38 | direct | 7909.3 | 0.0 | tool_output | get_inventory | 1 | call_HpywyGJNz4og1eufXKZOI9p4 | None | 314 |
| 39 | direct | 7909.4 | 0.0 | tool_output | get_weekly_demand | 1 | call_4ZpceCYx3nG5Hrogu04mNSEw | None | 357 |
| 40 | direct | 7909.5 | 0.1 | tool_output | get_inbound_shipments | 1 | call_000qE8knp61WSDEIRyGz5sWm | None | 379 |
| 41 | direct | 7909.5 | 0.0 | tool_output | get_inventory | 1 | call_1IMXBBwrBqSR70SkX2ZIDS7w | None | 312 |
| 42 | direct | 7909.6 | 0.0 | tool_output | get_weekly_demand | 1 | call_K4jj4GebFC0QWQ52bTYcJ9V5 | None | 357 |
| 43 | direct | 7909.7 | 0.0 | tool_output | get_inbound_shipments | 1 | call_lEhAKJUVz2DdT7MiUnlM9Un6 | None | 377 |
| 44 | direct | 7909.7 | 0.0 | tool_output | get_inventory | 1 | call_ubdiaVQ2wjcBr602G6jmSvsy | None | 313 |
| 45 | direct | 7909.8 | 0.0 | tool_output | get_weekly_demand | 1 | call_D3CuBUYsgGqJYQso8CPejmL1 | None | 357 |
| 46 | direct | 7909.8 | 0.0 | tool_output | get_inbound_shipments | 1 | call_FwmHX9APLCRiuqKYvgodahXT | None | 378 |
| 47 | direct | 7909.9 | 0.0 | tool_output | get_inventory | 1 | call_pC0chqEsmEN0k2fjizwJVm4L | None | 314 |
| 48 | direct | 7909.9 | 0.0 | tool_output | get_weekly_demand | 1 | call_PRWmEnRBD1BsSq8hbKuVJj4s | None | 357 |
| 49 | direct | 7910.0 | 0.0 | tool_output | get_inbound_shipments | 1 | call_bl2dKOM0nrF4n58bqUT4o08s | None | 378 |
| 50 | direct | 7910.1 | 0.0 | tool_output | get_inventory | 1 | call_by5BecRha4P3kJt0rE39bGGN | None | 312 |
| 51 | direct | 7910.1 | 0.0 | tool_output | get_weekly_demand | 1 | call_wsz43h13yR6R8APNdF8xkfBN | None | 357 |
| 52 | direct | 7910.2 | 0.0 | tool_output | get_inbound_shipments | 1 | call_lkHANlH9U95k3fUoHGUtID3b | None | 377 |
| 53 | direct | 7910.2 | 0.0 | tool_output | get_inventory | 1 | call_Hi3Z1vdKQmrKKB2bGDwwSqMb | None | 313 |
| 54 | direct | 7910.3 | 0.0 | tool_output | get_weekly_demand | 1 | call_YV7mX5njYuZRA2V2TK2TAfj6 | None | 357 |
| 55 | direct | 7910.3 | 0.0 | tool_output | get_inbound_shipments | 1 | call_tgs8GYcshE7CEMNLBudy0kYw | None | 379 |
| 56 | direct | 7910.4 | 0.0 | tool_output | get_inventory | 1 | call_XNZ5Ti340pXrTxt6RbGkMt8b | None | 314 |
| 57 | direct | 7910.4 | 0.0 | tool_output | get_weekly_demand | 1 | call_kfHgcTNw52FgooSLehk3zKid | None | 357 |
| 58 | direct | 7910.5 | 0.0 | tool_output | get_inbound_shipments | 1 | call_pTiZZjeeNTU2fBr0Czw9w1M6 | None | 378 |
| 59 | direct | 7910.5 | 0.0 | tool_output | get_inventory | 1 | call_rRwJpnjhVoTJoJ9qRnyoqVkM | None | 312 |
| 60 | direct | 7910.6 | 0.0 | tool_output | get_weekly_demand | 1 | call_3KyuzI3aHdUKCatAvKD8SLSC | None | 357 |
| 61 | direct | 7910.7 | 0.0 | tool_output | get_inbound_shipments | 1 | call_a4kZKb5z2FbGHgpRbEhvWVf9 | None | 376 |
| 62 | direct | 15872.5 | 7960.9 | model_request | request_2 | 2 | None | None | 26198 |
| 63 | direct | 15872.6 | 0.0 | assistant_message | final_assistant_message | 2 | None | None | 1046 |

## output 2

### Programmatic timeline

| sequence | arm | elapsed_ms | duration_ms | event | name | request | call_id | caller_id | payload_bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | programmatic | 31256.7 | 15383.0 | model_request | request_1 | 1 | None | None | 17061 |
| 2 | programmatic | 31256.8 | 0.0 | program | generated_program | 1 | call_o9pntNzvv05Tfgl4fy19scbn | None | 3949 |
| 3 | programmatic | 31256.9 | 0.0 | function_call | get_inventory | 1 | call_0H5JThjqcPzFJtHrK5skRu1D | call_o9pntNzvv05Tfgl4fy19scbn | 279 |
| 4 | programmatic | 31256.9 | 0.0 | function_call | get_weekly_demand | 1 | call_yF9H85xBP2hu1N85UrdvPXNk | call_o9pntNzvv05Tfgl4fy19scbn | 283 |
| 5 | programmatic | 31257.0 | 0.0 | function_call | get_inventory | 1 | call_0AI8H66SN390uhSIU06PISdL | call_o9pntNzvv05Tfgl4fy19scbn | 279 |
| 6 | programmatic | 31257.0 | 0.0 | function_call | get_weekly_demand | 1 | call_neglFzxXNXhxY4WD3Z7y2aDH | call_o9pntNzvv05Tfgl4fy19scbn | 283 |
| 7 | programmatic | 31257.0 | 0.0 | function_call | get_inventory | 1 | call_mnaTl0PKoytJWwyUoRO9WL5a | call_o9pntNzvv05Tfgl4fy19scbn | 279 |
| 8 | programmatic | 31257.1 | 0.0 | function_call | get_weekly_demand | 1 | call_pKTvnIZbjeR7BKAoBjFhiPbS | call_o9pntNzvv05Tfgl4fy19scbn | 283 |
| 9 | programmatic | 31257.1 | 0.0 | function_call | get_inventory | 1 | call_IakF4lgp95z0xqfdByRc10BG | call_o9pntNzvv05Tfgl4fy19scbn | 279 |
| 10 | programmatic | 31257.1 | 0.0 | function_call | get_weekly_demand | 1 | call_pbeTizm5QcbzxRxlyVHGPnzL | call_o9pntNzvv05Tfgl4fy19scbn | 283 |
| 11 | programmatic | 31257.2 | 0.0 | function_call | get_inventory | 1 | call_sSb7rnLsTqaDiAoy9KoePHKZ | call_o9pntNzvv05Tfgl4fy19scbn | 279 |
| 12 | programmatic | 31257.2 | 0.0 | function_call | get_weekly_demand | 1 | call_eARauHuyqSluyDTCk9CLkTU9 | call_o9pntNzvv05Tfgl4fy19scbn | 283 |
| 13 | programmatic | 31257.2 | 0.0 | function_call | get_inventory | 1 | call_i1HgdBvyP3qum0kp4yKpzAgv | call_o9pntNzvv05Tfgl4fy19scbn | 279 |
| 14 | programmatic | 31257.3 | 0.0 | function_call | get_weekly_demand | 1 | call_jkKdhwIDTBlPABDdXvnyQ01d | call_o9pntNzvv05Tfgl4fy19scbn | 283 |
| 15 | programmatic | 31257.3 | 0.0 | function_call | get_inventory | 1 | call_YRxhwLpwgLfWSVXQZEEUgaaF | call_o9pntNzvv05Tfgl4fy19scbn | 279 |
| 16 | programmatic | 31257.3 | 0.0 | function_call | get_weekly_demand | 1 | call_xj2NzxHQmKKfFUo7I10BAwtK | call_o9pntNzvv05Tfgl4fy19scbn | 283 |
| 17 | programmatic | 31257.4 | 0.0 | function_call | get_inventory | 1 | call_Am349ysAbmkVYGejp0u0aFgU | call_o9pntNzvv05Tfgl4fy19scbn | 279 |
| 18 | programmatic | 31257.4 | 0.0 | function_call | get_weekly_demand | 1 | call_iY3WCkT4mt8seT0ZSGRFfyyU | call_o9pntNzvv05Tfgl4fy19scbn | 283 |
| 19 | programmatic | 31257.4 | 0.0 | function_call | get_inventory | 1 | call_5GzAK27Xv3T2K0a1envBjEjs | call_o9pntNzvv05Tfgl4fy19scbn | 279 |
| 20 | programmatic | 31257.4 | 0.0 | function_call | get_weekly_demand | 1 | call_sposaGAmXblo85YouX58RunN | call_o9pntNzvv05Tfgl4fy19scbn | 283 |
| 21 | programmatic | 31257.5 | 0.0 | function_call | get_inventory | 1 | call_a7Ci1Sh8WPh3GfYzQAiUWGJx | call_o9pntNzvv05Tfgl4fy19scbn | 279 |
| 22 | programmatic | 31257.8 | 0.0 | function_call | get_weekly_demand | 1 | call_FAQtK4NgQhn4J7ns3ZIhY3fD | call_o9pntNzvv05Tfgl4fy19scbn | 285 |
| 23 | programmatic | 31258.0 | 0.0 | tool_output | get_inventory | 1 | call_0H5JThjqcPzFJtHrK5skRu1D | call_o9pntNzvv05Tfgl4fy19scbn | 370 |
| 24 | programmatic | 31258.1 | 0.0 | tool_output | get_weekly_demand | 1 | call_yF9H85xBP2hu1N85UrdvPXNk | call_o9pntNzvv05Tfgl4fy19scbn | 415 |
| 25 | programmatic | 31258.1 | 0.0 | tool_output | get_inventory | 1 | call_0AI8H66SN390uhSIU06PISdL | call_o9pntNzvv05Tfgl4fy19scbn | 371 |
| 26 | programmatic | 31258.2 | 0.0 | tool_output | get_weekly_demand | 1 | call_neglFzxXNXhxY4WD3Z7y2aDH | call_o9pntNzvv05Tfgl4fy19scbn | 415 |
| 27 | programmatic | 31258.2 | 0.0 | tool_output | get_inventory | 1 | call_mnaTl0PKoytJWwyUoRO9WL5a | call_o9pntNzvv05Tfgl4fy19scbn | 372 |
| 28 | programmatic | 31258.3 | 0.0 | tool_output | get_weekly_demand | 1 | call_pKTvnIZbjeR7BKAoBjFhiPbS | call_o9pntNzvv05Tfgl4fy19scbn | 415 |
| 29 | programmatic | 31258.3 | 0.0 | tool_output | get_inventory | 1 | call_IakF4lgp95z0xqfdByRc10BG | call_o9pntNzvv05Tfgl4fy19scbn | 370 |
| 30 | programmatic | 31258.4 | 0.0 | tool_output | get_weekly_demand | 1 | call_pbeTizm5QcbzxRxlyVHGPnzL | call_o9pntNzvv05Tfgl4fy19scbn | 415 |
| 31 | programmatic | 31258.5 | 0.0 | tool_output | get_inventory | 1 | call_sSb7rnLsTqaDiAoy9KoePHKZ | call_o9pntNzvv05Tfgl4fy19scbn | 371 |
| 32 | programmatic | 31258.5 | 0.0 | tool_output | get_weekly_demand | 1 | call_eARauHuyqSluyDTCk9CLkTU9 | call_o9pntNzvv05Tfgl4fy19scbn | 415 |
| 33 | programmatic | 31258.6 | 0.0 | tool_output | get_inventory | 1 | call_i1HgdBvyP3qum0kp4yKpzAgv | call_o9pntNzvv05Tfgl4fy19scbn | 372 |
| 34 | programmatic | 31258.6 | 0.0 | tool_output | get_weekly_demand | 1 | call_jkKdhwIDTBlPABDdXvnyQ01d | call_o9pntNzvv05Tfgl4fy19scbn | 415 |
| 35 | programmatic | 31258.7 | 0.0 | tool_output | get_inventory | 1 | call_YRxhwLpwgLfWSVXQZEEUgaaF | call_o9pntNzvv05Tfgl4fy19scbn | 370 |
| 36 | programmatic | 31258.7 | 0.0 | tool_output | get_weekly_demand | 1 | call_xj2NzxHQmKKfFUo7I10BAwtK | call_o9pntNzvv05Tfgl4fy19scbn | 415 |
| 37 | programmatic | 31258.8 | 0.0 | tool_output | get_inventory | 1 | call_Am349ysAbmkVYGejp0u0aFgU | call_o9pntNzvv05Tfgl4fy19scbn | 371 |
| 38 | programmatic | 31258.8 | 0.0 | tool_output | get_weekly_demand | 1 | call_iY3WCkT4mt8seT0ZSGRFfyyU | call_o9pntNzvv05Tfgl4fy19scbn | 415 |
| 39 | programmatic | 31258.9 | 0.0 | tool_output | get_inventory | 1 | call_5GzAK27Xv3T2K0a1envBjEjs | call_o9pntNzvv05Tfgl4fy19scbn | 372 |
| 40 | programmatic | 31258.9 | 0.0 | tool_output | get_weekly_demand | 1 | call_sposaGAmXblo85YouX58RunN | call_o9pntNzvv05Tfgl4fy19scbn | 415 |
| 41 | programmatic | 31259.0 | 0.0 | tool_output | get_inventory | 1 | call_a7Ci1Sh8WPh3GfYzQAiUWGJx | call_o9pntNzvv05Tfgl4fy19scbn | 370 |
| 42 | programmatic | 31259.0 | 0.0 | tool_output | get_weekly_demand | 1 | call_FAQtK4NgQhn4J7ns3ZIhY3fD | call_o9pntNzvv05Tfgl4fy19scbn | 415 |
| 43 | programmatic | 33170.7 | 1910.5 | model_request | request_2 | 2 | None | None | 28578 |
| 44 | programmatic | 33170.8 | 0.0 | function_call | get_inbound_shipments | 2 | call_42uUFvwLMiYjgSExtjDrLw8d | call_o9pntNzvv05Tfgl4fy19scbn | 287 |
| 45 | programmatic | 33170.8 | 0.0 | function_call | get_inbound_shipments | 2 | call_ommRXBT8fCZoSpoByagq0zyE | call_o9pntNzvv05Tfgl4fy19scbn | 287 |
| 46 | programmatic | 33170.9 | 0.0 | function_call | get_inbound_shipments | 2 | call_RRldMbGswHRJqrKgCdQgfzfg | call_o9pntNzvv05Tfgl4fy19scbn | 287 |
| 47 | programmatic | 33170.9 | 0.0 | function_call | get_inbound_shipments | 2 | call_w7tXVZV7gZIU1rn8WtvcGAII | call_o9pntNzvv05Tfgl4fy19scbn | 287 |
| 48 | programmatic | 33170.9 | 0.0 | function_call | get_inbound_shipments | 2 | call_mV4oo9KDbTsBtQYllLqkVvYF | call_o9pntNzvv05Tfgl4fy19scbn | 287 |
| 49 | programmatic | 33171.0 | 0.0 | function_call | get_inbound_shipments | 2 | call_GauDtEIRVkblYEAbHqd15r1H | call_o9pntNzvv05Tfgl4fy19scbn | 287 |
| 50 | programmatic | 33171.0 | 0.0 | function_call | get_inbound_shipments | 2 | call_GuqR5R9zVLXKaoBCoU8F290y | call_o9pntNzvv05Tfgl4fy19scbn | 287 |
| 51 | programmatic | 33171.0 | 0.0 | function_call | get_inbound_shipments | 2 | call_V1nbfWqB0YfhCtZm4gZMAooq | call_o9pntNzvv05Tfgl4fy19scbn | 287 |
| 52 | programmatic | 33171.1 | 0.0 | function_call | get_inbound_shipments | 2 | call_8VZLUMiKUyxNySMFF3fe6SkP | call_o9pntNzvv05Tfgl4fy19scbn | 287 |
| 53 | programmatic | 33171.1 | 0.0 | function_call | get_inbound_shipments | 2 | call_4vag0jDCJWHAkSuZ4oN3Ug0q | call_o9pntNzvv05Tfgl4fy19scbn | 289 |
| 54 | programmatic | 33171.3 | 0.1 | tool_output | get_inbound_shipments | 2 | call_42uUFvwLMiYjgSExtjDrLw8d | call_o9pntNzvv05Tfgl4fy19scbn | 434 |
| 55 | programmatic | 33171.4 | 0.0 | tool_output | get_inbound_shipments | 2 | call_ommRXBT8fCZoSpoByagq0zyE | call_o9pntNzvv05Tfgl4fy19scbn | 436 |
| 56 | programmatic | 33171.4 | 0.0 | tool_output | get_inbound_shipments | 2 | call_RRldMbGswHRJqrKgCdQgfzfg | call_o9pntNzvv05Tfgl4fy19scbn | 437 |
| 57 | programmatic | 33171.5 | 0.0 | tool_output | get_inbound_shipments | 2 | call_w7tXVZV7gZIU1rn8WtvcGAII | call_o9pntNzvv05Tfgl4fy19scbn | 435 |
| 58 | programmatic | 33171.6 | 0.0 | tool_output | get_inbound_shipments | 2 | call_mV4oo9KDbTsBtQYllLqkVvYF | call_o9pntNzvv05Tfgl4fy19scbn | 436 |
| 59 | programmatic | 33171.6 | 0.0 | tool_output | get_inbound_shipments | 2 | call_GauDtEIRVkblYEAbHqd15r1H | call_o9pntNzvv05Tfgl4fy19scbn | 436 |
| 60 | programmatic | 33171.7 | 0.0 | tool_output | get_inbound_shipments | 2 | call_GuqR5R9zVLXKaoBCoU8F290y | call_o9pntNzvv05Tfgl4fy19scbn | 435 |
| 61 | programmatic | 33171.8 | 0.0 | tool_output | get_inbound_shipments | 2 | call_V1nbfWqB0YfhCtZm4gZMAooq | call_o9pntNzvv05Tfgl4fy19scbn | 437 |
| 62 | programmatic | 33171.8 | 0.0 | tool_output | get_inbound_shipments | 2 | call_8VZLUMiKUyxNySMFF3fe6SkP | call_o9pntNzvv05Tfgl4fy19scbn | 436 |
| 63 | programmatic | 33171.9 | 0.0 | tool_output | get_inbound_shipments | 2 | call_4vag0jDCJWHAkSuZ4oN3Ug0q | call_o9pntNzvv05Tfgl4fy19scbn | 434 |
| 64 | programmatic | 39489.1 | 6316.0 | model_request | request_3 | 3 | None | None | 36450 |
| 65 | programmatic | 39489.2 | 0.0 | program_output | program_output | 3 | call_o9pntNzvv05Tfgl4fy19scbn | None | 643 |
| 66 | programmatic | 39489.2 | 0.0 | assistant_message | final_assistant_message | 3 | None | None | 1028 |
