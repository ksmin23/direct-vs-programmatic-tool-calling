# Inventory small — Normalized semantic timeline

- Source notebook: `notebooks/00_inventory_tool_call_trace.ipynb`
- Execution cell: 10 (`timeline`)
- Dataset name: `inventory`
- Dataset size: `small`
- Case ID: `inventory-small`
- SKU count: 3
- Execution date: `2026-08-07` (`Asia/Seoul`)

## output 1

### Direct timeline

| sequence | arm | elapsed_ms | duration_ms | event | name | request | call_id | caller_id | payload_bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | direct | 6617.4 | 5701.1 | model_request | request_1 | 1 | None | None | 7354 |
| 2 | direct | 6617.5 | 0.0 | function_call | get_inventory | 1 | call_tLvbiC6DmyKDV4Ju8sEEnaMx | None | 207 |
| 3 | direct | 6617.5 | 0.0 | function_call | get_weekly_demand | 1 | call_UiKU1sFLQNVcP0ewSb5IzeAi | None | 211 |
| 4 | direct | 6617.5 | 0.0 | function_call | get_inbound_shipments | 1 | call_72qWYkhEWXdesUJN4N6VL8sV | None | 215 |
| 5 | direct | 6617.5 | 0.0 | function_call | get_inventory | 1 | call_Yt0CWAMBqfXDk1MVm8MAyu0X | None | 207 |
| 6 | direct | 6617.5 | 0.0 | function_call | get_weekly_demand | 1 | call_FAIJLsL01PsFashbMu1lx4qqL | None | 211 |
| 7 | direct | 6617.5 | 0.0 | function_call | get_inbound_shipments | 1 | call_DStIiNIAXKtPkL1dp4pMnUvE | None | 215 |
| 8 | direct | 6617.5 | 0.0 | function_call | get_inventory | 1 | call_Cf3QZvYsBWrGbhzjNUfU3afk | None | 207 |
| 9 | direct | 6617.6 | 0.0 | function_call | get_weekly_demand | 1 | call_NAScNBGcXB0ZsKlnTmBybkZl | None | 211 |
| 10 | direct | 6617.6 | 0.0 | function_call | get_inbound_shipments | 1 | call_YnVPw6e0cyXfASMqmsJ5YGFd | None | 215 |
| 11 | direct | 6617.6 | 0.0 | tool_output | get_inventory | 1 | call_tLvbiC6DmyKDV4Ju8sEEnaMx | None | 312 |
| 12 | direct | 6617.7 | 0.0 | tool_output | get_weekly_demand | 1 | call_UiKU1sFLQNVcP0ewSb5IzeAi | None | 357 |
| 13 | direct | 6617.7 | 0.0 | tool_output | get_inbound_shipments | 1 | call_72qWYkhEWXdesUJN4N6VL8sV | None | 376 |
| 14 | direct | 6617.7 | 0.0 | tool_output | get_inventory | 1 | call_Yt0CWAMBqfXDk1MVm8MAyu0X | None | 313 |
| 15 | direct | 6617.8 | 0.0 | tool_output | get_weekly_demand | 1 | call_FAIJLsL01PsFashbMu1lx4qqL | None | 357 |
| 16 | direct | 6617.8 | 0.0 | tool_output | get_inbound_shipments | 1 | call_DStIiNIAXKtPkL1dp4pMnUvE | None | 378 |
| 17 | direct | 6617.8 | 0.0 | tool_output | get_inventory | 1 | call_Cf3QZvYsBWrGbhzjNUfU3afk | None | 314 |
| 18 | direct | 6617.8 | 0.0 | tool_output | get_weekly_demand | 1 | call_NAScNBGcXB0ZsKlnTmBybkZl | None | 357 |
| 19 | direct | 6617.9 | 0.0 | tool_output | get_inbound_shipments | 1 | call_YnVPw6e0cyXfASMqmsJ5YGFd | None | 379 |
| 20 | direct | 11630.2 | 5009.6 | model_request | request_2 | 2 | None | None | 12757 |
| 21 | direct | 11630.4 | 0.0 | assistant_message | final_assistant_message | 2 | None | None | 507 |

## output 2

### Programmatic timeline

| sequence | arm | elapsed_ms | duration_ms | event | name | request | call_id | caller_id | payload_bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | programmatic | 20521.8 | 8890.2 | model_request | request_1 | 1 | None | None | 13827 |
| 2 | programmatic | 20521.9 | 0.0 | program | generated_program | 1 | call_E6zYZelHPd1vQSQwR8nj66tc | None | 4766 |
| 3 | programmatic | 20522.0 | 0.0 | function_call | get_inventory | 1 | call_Se0qILXaYxJNQiK3RuRp8uIg | call_E6zYZelHPd1vQSQwR8nj66tc | 279 |
| 4 | programmatic | 20522.0 | 0.0 | function_call | get_inventory | 1 | call_dGZrD8DmvNHQy1VI6TQZCx6l | call_E6zYZelHPd1vQSQwR8nj66tc | 279 |
| 5 | programmatic | 20522.0 | 0.0 | function_call | get_inventory | 1 | call_ZdEQPFzkP9Tw4QzlCX1lluXJ | call_E6zYZelHPd1vQSQwR8nj66tc | 279 |
| 6 | programmatic | 20522.2 | 0.0 | function_call | get_weekly_demand | 1 | call_aiKSyd58nRixVtmVtVEKRFUj | call_E6zYZelHPd1vQSQwR8nj66tc | 283 |
| 7 | programmatic | 20522.2 | 0.0 | function_call | get_weekly_demand | 1 | call_eWRmU2Tk6LdRPqfTNuEUxm7I | call_E6zYZelHPd1vQSQwR8nj66tc | 283 |
| 8 | programmatic | 20522.3 | 0.0 | function_call | get_weekly_demand | 1 | call_rNIZnzzcCd2KeiZVrGWCP7fW | call_E6zYZelHPd1vQSQwR8nj66tc | 285 |
| 9 | programmatic | 20522.5 | 0.1 | tool_output | get_inventory | 1 | call_Se0qILXaYxJNQiK3RuRp8uIg | call_E6zYZelHPd1vQSQwR8nj66tc | 370 |
| 10 | programmatic | 20522.6 | 0.1 | tool_output | get_inventory | 1 | call_dGZrD8DmvNHQy1VI6TQZCx6l | call_E6zYZelHPd1vQSQwR8nj66tc | 371 |
| 11 | programmatic | 20522.7 | 0.0 | tool_output | get_inventory | 1 | call_ZdEQPFzkP9Tw4QzlCX1lluXJ | call_E6zYZelHPd1vQSQwR8nj66tc | 372 |
| 12 | programmatic | 20522.8 | 0.1 | tool_output | get_weekly_demand | 1 | call_aiKSyd58nRixVtmVtVEKRFUj | call_E6zYZelHPd1vQSQwR8nj66tc | 415 |
| 13 | programmatic | 20522.9 | 0.0 | tool_output | get_weekly_demand | 1 | call_eWRmU2Tk6LdRPqfTNuEUxm7I | call_E6zYZelHPd1vQSQwR8nj66tc | 415 |
| 14 | programmatic | 20522.9 | 0.0 | tool_output | get_weekly_demand | 1 | call_rNIZnzzcCd2KeiZVrGWCP7fW | call_E6zYZelHPd1vQSQwR8nj66tc | 415 |
| 15 | programmatic | 21274.4 | 750.4 | model_request | request_2 | 2 | None | None | 16663 |
| 16 | programmatic | 21274.6 | 0.0 | function_call | get_inbound_shipments | 2 | call_MjWfIbtZaqTkfZPCeWbUines | call_E6zYZelHPd1vQSQwR8nj66tc | 289 |
| 17 | programmatic | 21274.9 | 0.1 | tool_output | get_inbound_shipments | 2 | call_MjWfIbtZaqTkfZPCeWbUines | call_E6zYZelHPd1vQSQwR8nj66tc | 434 |
| 18 | programmatic | 22573.9 | 1298.2 | model_request | request_3 | 3 | None | None | 17438 |
| 19 | programmatic | 22574.0 | 0.0 | function_call | get_inbound_shipments | 3 | call_N1tmyCQs7B3YpnMSlu2MGmft | call_E6zYZelHPd1vQSQwR8nj66tc | 289 |
| 20 | programmatic | 22574.2 | 0.1 | tool_output | get_inbound_shipments | 3 | call_N1tmyCQs7B3YpnMSlu2MGmft | call_E6zYZelHPd1vQSQwR8nj66tc | 436 |
| 21 | programmatic | 23458.3 | 883.4 | model_request | request_4 | 4 | None | None | 18215 |
| 22 | programmatic | 23458.4 | 0.0 | function_call | get_inbound_shipments | 4 | call_oK3GDRrFtsQFrRT9LM3FUcFs | call_E6zYZelHPd1vQSQwR8nj66tc | 289 |
| 23 | programmatic | 23458.5 | 0.1 | tool_output | get_inbound_shipments | 4 | call_oK3GDRrFtsQFrRT9LM3FUcFs | call_E6zYZelHPd1vQSQwR8nj66tc | 437 |
| 24 | programmatic | 26154.2 | 2694.7 | model_request | request_5 | 5 | None | None | 20795 |
| 25 | programmatic | 26154.3 | 0.0 | program_output | program_output | 5 | call_E6zYZelHPd1vQSQwR8nj66tc | None | 318 |
| 26 | programmatic | 26154.3 | 0.0 | assistant_message | final_assistant_message | 5 | None | None | 527 |
