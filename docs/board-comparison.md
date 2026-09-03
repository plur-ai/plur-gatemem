# Board comparison — PLUR MGS vs official GateMem ledger (interim)

| Backbone | Domain | PLUR | Best ext-mem (board) | Long-Context (board) | PLUR rank in ext-mem class |
|---|---|---|---|---|---|
| GPT-4o-mini | Medical | **23.6** | 16.4 | 45.6 | #1 of 5 |
| GPT-4o-mini | Office | **12.2** | 9.8 | 20.1 | #1 of 5 |
| GPT-4o-mini | Education | **4.9** | 4.9 | 23.1 | #1 of 5 |
| GPT-4o-mini | Household | **15.0** | 27.4 | 30.0 | #2 of 5 |
| Gemini-2.5-Flash-Lite | Medical | **19.0** | 13.8 | 45.7 | #1 of 5 |
| Gemini-2.5-Flash-Lite | Office | **24.5** | 11.6 | 9.6 | #1 of 5 |
| Gemini-2.5-Flash-Lite | Education | **15.3** | 11.6 | 22.4 | #1 of 5 |
| Gemini-2.5-Flash-Lite | Household | **20.4** | 13.7 | 29.5 | #1 of 5 |
| Llama-4-Maverick | Medical | **32.4** | 23.5 | 56.7 | #1 of 5 |
| Llama-4-Maverick | Office | **39.3** | 28.1 | 33.3 | #1 of 5 |
| Llama-4-Maverick | Education | **15.7** | 9.6 | 46.6 | #1 of 5 |
| Llama-4-Maverick | Household | **40.5** | 32.5 | 51.8 | #1 of 5 |
| GPT-5-mini | Medical | **39.9** | 27.3 | 54.8 | #1 of 5 |
| GPT-5-mini | Office | **52.4** | 43.2 | 58.9 | #1 of 5 |
| GPT-5-mini | Education | **28.8** | 22.6 | 60.5 | #1 of 5 |
| GPT-5-mini | Household | **53.0** | 31.6 | 49.4 | #1 of 5 |
| Deepseek-V4-Pro | Medical | **47.6** | 45.9 | 70.6 | #1 of 5 |
| Deepseek-V4-Pro | Office | **57.5** | 52.4 | 67.9 | #1 of 5 |
| Deepseek-V4-Pro | Education | **30.7** | 16.7 | 71.0 | #1 of 5 |
| Deepseek-V4-Pro | Household | **50.1** | 38.8 | 68.5 | #1 of 5 |

PLUR beats the best published external-memory baseline in **18 of 20** backbone×domain cells with board comparators.

Note: GPT-5.6-sol has no board baselines (newer than the paper); our runs are self-reported tier with recorded config deviations (see manifest.json).