# Board comparison — PLUR MGS vs official GateMem ledger (FINAL, all 6 backbones + base)

| Backbone | Domain | PLUR MGS (U/A/F) | Best ext-mem (board) | Long-Context (board) | PLUR ext-mem rank |
|---|---|---|---|---|---|
| GPT-4o-mini | Medical | **23.6** (53.8/50.0/12.4) | A-Mem 16.4 | 45.6 | #1 of 5 |
| GPT-4o-mini | Office | **12.2** (26.6/46.2/14.9) | Mem0 9.8 | 20.1 | #1 of 5 |
| GPT-4o-mini | Education | **4.9** (7.8/22.2/18.9) | A-Mem 4.9 | 23.1 | #1 of 5 |
| GPT-4o-mini | Household | **15.0** (20.1/13.6/13.6) | Mem0 27.4 | 30.0 | #2 of 5 |
| Gemini-2.5-Flash-Lite | Medical | **19.0** (82.4/55.7/48.0) | A-Mem 13.8 | 45.7 | #1 of 5 |
| Gemini-2.5-Flash-Lite | Office | **24.5** (79.2/59.6/23.4) | ReMem-I 11.6 | 9.6 | #1 of 5 |
| Gemini-2.5-Flash-Lite | Education | **15.3** (54.4/36.7/55.6) | Mem0 11.6 | 22.4 | #1 of 5 |
| Gemini-2.5-Flash-Lite | Household | **20.4** (62.0/32.6/51.1) | ReMem-I 13.7 | 29.5 | #1 of 5 |
| Llama-4-Maverick | Medical | **32.4** (79.5/42.7/28.8) | A-Mem 23.5 | 56.7 | #1 of 5 |
| Llama-4-Maverick | Office | **39.3** (74.0/33.3/20.3) | ReMem-I 28.1 | 33.3 | #1 of 5 |
| Llama-4-Maverick | Education | **15.7** (35.0/16.7/46.1) | A-Mem 9.6 | 46.6 | #1 of 5 |
| Llama-4-Maverick | Household | **40.5** (58.2/9.8/22.8) | A-Mem 32.5 | 51.8 | #1 of 5 |
| GPT-5-mini | Medical | **39.9** (62.9/25.5/14.7) | A-Mem 27.3 | 54.8 | #1 of 5 |
| GPT-5-mini | Office | **52.4** (81.8/31.0/7.2) | ReMem-I 43.2 | 58.9 | #1 of 5 |
| GPT-5-mini | Education | **28.8** (48.3/15.6/29.4) | Mem0 22.6 | 60.5 | #1 of 5 |
| GPT-5-mini | Household | **53.0** (71.2/19.0/8.2) | A-Mem 31.6 | 49.4 | #1 of 5 |
| Deepseek-V4-Pro | Medical | **47.6** (65.7/19.8/9.6) | A-Mem 45.9 | 70.6 | #1 of 5 |
| Deepseek-V4-Pro | Office | **57.5** (83.8/21.1/13.1) | A-Mem 52.4 | 67.9 | #1 of 5 |
| Deepseek-V4-Pro | Education | **30.7** (42.8/8.9/21.1) | A-Mem 16.7 | 71.0 | #1 of 5 |
| Deepseek-V4-Pro | Household | **50.1** (66.8/16.8/9.8) | A-Mem 38.8 | 68.5 | #1 of 5 |
| GPT-5.4 | Medical | **49.8** (71.0/21.9/10.2) | A-Mem 46.6 | 80.1 | #1 of 5 |
| GPT-5.4 | Office | **49.8** (79.2/29.8/10.4) | A-Mem 48.3 | 56.5 | #1 of 5 |
| GPT-5.4 | Education | **25.9** (42.8/10.0/32.8) | Mem0 21.1 | 68.8 | #1 of 5 |
| GPT-5.4 | Household | **45.5** (63.0/18.5/11.4) | A-Mem 36.4 | 54.0 | #1 of 5 |
| GPT-5.6-sol | Medical | **42.4** (47.6/10.9/0.0) | - | - | no baselines |
| GPT-5.6-sol | Office | **63.4** (76.6/15.8/1.8) | - | - | no baselines |
| GPT-5.6-sol | Education | **30.2** (34.4/5.6/7.2) | - | - | no baselines |
| GPT-5.6-sol | Household | **54.8** (67.9/14.7/5.4) | - | - | no baselines |

## Summary

- PLUR is the **#1 external-memory method in 22 of 24** board-comparable backbone×domain cells.
- PLUR beats even Long-Context (full-transcript) in 3 cells — at a fraction of its token cost.
- Per-backbone PLUR MGS means: GPT-4o-mini 13.9, Gemini-2.5-Flash-Lite 19.8, Llama-4-Maverick 32.0, GPT-5-mini 43.5, Deepseek-V4-Pro 46.5, GPT-5.4 42.8, GPT-5.6-sol 47.7
- GPT-5.6-sol medical achieved **F = 0.0** — zero forgetting failures across all deletion-recovery attacks (first perfect forgetting score in the evaluation).

Self-reported tier; config deviations recorded in manifest.json; artifacts hashed per run.