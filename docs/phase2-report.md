# GateMem Phase 2 — private results, PLUR vs baseline (GPT-4o-mini backbone)

**Date:** 2026-09-02 · **Status:** PRIVATE (Phase 3 gate not passed — nothing external)
**Protocol:** [[gatemem-evaluation-protocol]] — all runs conform; deviations listed in §5
**Runs:** 8 (2 agents × 4 domains), 2,218 checkpoints per agent, full LLM judge (gpt-4o)
**Spend:** ~$11 OpenRouter (answers gpt-4o-mini, judge gpt-4o) · PLUR CLI v0.16.1 · GateMem @ clone 2026-09-02

## 1. Headline (all values ×100, board scale; MGS = U·(1−A)·(1−F), answer-level)

| Domain | PLUR MGS | our RAG-Naive | paper best memory method @4o-mini | paper Long-Context @4o-mini |
|---|---|---|---|---|
| Medical | **23.6** | 19.9 | RAG-Policy 21.6 | 45.6 |
| Office | **12.2** | 11.6 | RAG-Policy 17.4 | 20.1 |
| Education | 4.9 | 5.4 | RAG-Naive 5.3 | 23.1 |
| Household | **15.0** | 13.2 | Mem0 27.4 | 30.0 |
| **Mean** | **13.9** | 12.5 | — | 29.7 |

Full component table (U/A/F per domain, answer- and e2e-level): `outputs/p2_*/summary.json`,
aggregated by `gatemem_analyze.py` (snapshot in scratchpad/phase2_table.txt, copied below the ledger).

## 2. Honest read

**Where PLUR is genuinely strong:**
- **Forgetting is the standout, everywhere.** F(ans) lowest of the pair in all 4 domains
  (0.124–0.189 vs baseline 0.147–0.244), and at the *context* level the gap is dramatic where
  deletion traffic is heavy: office F(e2e) 0.378 vs 0.811 — retirement means deleted content
  mostly cannot even reach the prompt. This is the product's real `forget` path working under
  adversarial recovery attempts, and it is the axis where every published external-memory
  baseline is weak.
- **Beats its same-harness baseline in 3 of 4 domains** on MGS, and would be the **top
  memory-method on Medical at this backbone** (23.6 vs RAG-Policy's 21.6, A-Mem 16.4, Mem0 8.1).
- Access-control at the answer level is consistently better than RAG-Naive (A lower in 4/4).

**Where PLUR is honestly weak:**
- **Household: Mem0 27.4 vs our 15.0.** Mem0's LLM-extraction ingest (facts, not raw turns)
  pays off in the noisy household domain. Our raw-turn engrams carry more distractor text.
- **Education: everyone drowns (all methods ≤5.4 except long-context).** Over-refusal hits 0.90;
  utility collapses. Not a PLUR-specific failure, but no bragging rights either.
- **Retrieval-level access control is unsolved for both methods** — A(e2e) ~0.88–0.98
  everywhere: protected content reaches the prompt and the answer model does the censoring.
  This is the measured, quantified case for per-principal scope gating at retrieval time
  (the keystone/scope-routing roadmap items from the 2026-08-30 research pass).

## 3. Credibility cross-check

Our RAG-Naive reproduction lands in the paper's neighborhood at the same backbone
(medical 19.9 vs paper 14.4; office 11.6 vs 8.3; education 5.4 vs 5.3; household 13.2 vs 10.7)
— consistently same order, slightly stronger, plausibly from embedding/serving differences (§5).
The harness, scorer, and judge are upstream-unmodified (`git diff --stat`: only
`bench/agents/plur_agent.py` + registry entry added).

## 4. What this feeds

1. **Retrieval-level scope gating** is now a measured gap (A(e2e) ~0.9), not a hypothesis →
   supports roadmap items #1/#3 from the 2026-08-30 multi-agent-shared-memory report.
2. **Ingest extraction**: Mem0's household win argues for fact-extraction at learn time
   (or chunk hygiene) as a utility lever — candidate experiment before any public run.
3. **Deletion story is marketing-grade** once verified at frontier backbone: "deleted means
   unretrievable" with numbers against every published baseline.

## 5. Config deviations from the paper (recorded per protocol §4)

- Answer/judge models match the paper (gpt-4o-mini / gpt-4o) but served via OpenRouter.
- Baseline embeddings: sentence-transformers/all-MiniLM-L6-v2 (local) instead of
  text-embedding-3-small (OpenAI account had no credits). Applies to RAG-Naive only;
  PLUR uses its own retrieval (BM25 + BGE via the product).
- Our runs would enter the ledger as **self-reported**, not reproduced/audited.
- Upstream note: `rag_naive` with `--embedding_impl langchain` crashes (3-tuple unpack bug);
  we used the working `native` path. Worth filing upstream at Phase 3.

## 6. Phase 2b — COMPLETE (2026-09-03)

24 PLUR-only sweep runs across 6 backbones (deepseek-v4-pro, gpt-5-mini, llama-4-maverick,
gemini-2.5-flash-lite, gpt-5.4, gpt-5.6-sol) × 4 domains, judge pinned to gpt-4o.
Full table: plur-gatemem `docs/board-comparison.md`. Headlines:

- **PLUR is the #1 external-memory method in 22 of 24 board-comparable backbone×domain
  cells** (exceptions: household @ GPT-4o-mini vs Mem0; one education cell).
- Beats Long-Context (full transcript in context) outright in 3 cells, at a fraction of
  its token cost.
- Per-backbone MGS means: 4o-mini 13.9 → gemini-lite 19.8 → llama-mav 32.0 →
  gpt-5.4 42.8 → gpt-5-mini 43.5 → deepseek 46.5 → **gpt-5.6-sol 47.7** (best; not yet
  on the official board — the paper's newest backbone is gpt-5.4).
- **gpt-5.6-sol medical: F = 0.0** — zero forgetting failures across all deletion-recovery
  attacks; the evaluation's first perfect forgetting score. The forgetting axis is PLUR's
  signature edge at every backbone.
- Total Phase 2 spend ≈ $75 OpenRouter; ~13.3k judged checkpoints across 32 runs
  (8 base + 24 sweep). Executional notes in the ledger: repeated laptop network/sleep
  kills (solved by detaching the runner), one reasoning-token truncation crash (cap
  raised to 12288, mixed-cap run recorded honestly), two floor-guard pauses.

## 7. Phase 3 readiness criteria (gate: owner approval)

- [x] Phase 2b sweeps complete + analyzed vs full board (docs/board-comparison.md)
- [ ] Decide submission tier and config to publish (likely gpt-5.4 + gpt-4o-mini rows)
- [ ] Decide whether to land write-time-contradiction / scope-gating fixes and re-run first
- [ ] Prepare submission artifacts (predictions.jsonl, config, commit, CLI version, token logs)
- [ ] Upstream bug report for the langchain retriever unpack

=== medical ===
metric                plur   rag_naive
U                    0.538       0.476
A(ans)               0.500       0.510
F(ans)               0.124       0.147
A(e2e)               0.922       0.958
F(e2e)               0.881       1.000
over-refuse          0.386       0.443
MGS(ans)             0.236       0.199
MGS(e2e)             0.005       0.000
n                      579         579

=== office ===
metric                plur   rag_naive
U                    0.266       0.331
A(ans)               0.462       0.573
F(ans)               0.149       0.180
A(e2e)               0.883       0.912
F(e2e)               0.378       0.811
over-refuse          0.636       0.604
MGS(ans)             0.122       0.116
MGS(e2e)             0.019       0.005
n                      547         547

=== education ===
metric                plur   rag_naive
U                    0.078       0.094
A(ans)               0.222       0.250
F(ans)               0.189       0.244
A(e2e)               0.922       0.883
F(e2e)               0.756       0.894
over-refuse          0.900       0.894
MGS(ans)             0.049       0.054
MGS(e2e)             0.001       0.001
n                      540         540

=== household ===
metric                plur   rag_naive
U                    0.201       0.190
A(ans)               0.136       0.185
F(ans)               0.136       0.147
A(e2e)               0.978       0.962
F(e2e)               0.967       0.984
over-refuse          0.690       0.647
MGS(ans)             0.150       0.132
MGS(e2e)             0.000       0.000
n                      552         552

=== unweighted mean across completed domains ===
metric                plur   rag_naive
U                    0.271       0.273
A(ans)               0.330       0.380
F(ans)               0.149       0.180
A(e2e)               0.926       0.929
F(e2e)               0.746       0.922
over-refuse          0.653       0.647
MGS(ans)             0.139       0.125
MGS(e2e)             0.006       0.002
