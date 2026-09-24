# GateMem Evaluation Protocol — clean-room rules for the PLUR run

**Status:** binding for all PLUR GateMem runs (private and any future public claim)
**Created:** 2026-09-02 · Owner: Gregor · Prepared during Phase 0/1 build
**Benchmark:** GateMem (arXiv:2606.18829), repo `rzhub/GateMem`, data CC BY 4.0 (shipped in-repo)
**Goal per owner directive (2026-09-02):** "in the most honest way, build all guardrails. We honestly want to know how we score, then we can improve. First spot will be earned."

## 1. What we are measuring

Whether PLUR — the real released product, not a benchmark special — can serve as the memory
layer of a multi-principal shared-memory agent and score honestly on GateMem's three axes:
utility (U), access-control violation rate (A), active-forgetting failure rate (F);
MGS = U · (1−A) · (1−F).

## 2. Clean-room rules (hidden-field discipline)

The GateMem README: methods must not use hidden annotation fields. Binding rules for our agent:

1. The PLUR agent may read ONLY: episode turns as streamed by the harness (`turn_id`,
   `timestamp`, `speaker`, `turn_kind`, `text`), and at query time the checkpoint's visible
   fields: `checkpoint_id`, `asker_principal_id`, `asker_role`, `query_type`, `query_text`.
2. NEVER read: `expected_action`, `judge_spec`, `leak_targets`, `attack_type`,
   `gold_answer_structured`, episode `records` annotations (canonical values/regex).
   The base class uses episode `records` for its internal audit trace only — that is harness
   machinery shared by all baselines and is never exposed to the answer LLM; we do not use it
   for retrieval, filtering, or answering.
3. No checkpoint may influence ingestion (no peeking ahead); the agent processes turns in
   stream order, checkpoints fire at their `as_of_turn_id` exactly as the runner dictates.
4. The answer prompt is the harness's own standardized template (`bench/prompts/query_prompt.txt`)
   — same policy block, same relationship-facts filtering as every baseline. No custom prompt
   engineering unique to our agent in v1; any later prompt change must be documented here and
   applied only via the harness's declared configuration surface.

## 3. Real-product rule

5. Memory operations go through the released PLUR surface: the `@plur-ai/cli` binary via the
   `plur_ai` Python SDK (`learn`, `recall`/`recall_hybrid`, `forget`, `status`). No direct
   YAML writes, no reaching into internals, no benchmark-only retrieval path. The CLI version
   used is recorded in every run's metadata. If the eval finds a product bug, the fix ships in
   the product first and the run re-executes on the released fix.
6. Store isolation: every episode gets a fresh, throwaway PLUR store under the run's temp
   directory (`PLUR_PATH` override). The eval never touches `~/.plur` or any real store.
7. Deletion requests arrive as natural language inside turns (e.g. "please delete the
   temporary safe numbers"). The agent's deletion-intent handling is part of the system
   under test: it may use heuristics plus PLUR's own recall to locate targets and
   `plur forget` by exact engram id. Deletion-request turns are never themselves stored
   verbatim as memory content (they contain the very values being deleted); only a sanitized
   deletion marker without sensitive values may be stored. Forgotten = retired via the product's
   real retirement path; if retired engrams remain retrievable, that is a product bug to fix,
   not an adapter patch to hide.

## 4. Fair-comparison rules

8. Answer model, judge model, temperature, top_k and all shared harness settings are identical
   across PLUR and every baseline we run. Any deviation from the paper's config
   (gpt-4o-mini answers / gpt-4o judge / text-embedding-3-small) is recorded in the run log
   and repeated identically for all methods in that comparison set.
9. Baselines are run from the unmodified upstream harness. Our only repo modifications:
   adding `bench/agents/plur_agent.py`, its registry entry, and CLI wiring. The runner,
   scorer, judge, and prompts are untouched — verified by `git diff --stat` recorded per run.
10. We report the numbers we get. No cherry-picking domains, no re-rolling seeds until scores
    look good, no silently dropping failed checkpoints. Every run (including bad ones) is
    logged under `outputs/` with its full config, git commit, CLI version, and token usage.

## 5. Phase gate

11. Phases 0–2 are private. Nothing is submitted to the leaderboard, published, or cited
    externally without explicit owner approval (Phase 3 gate). Improvement iterations happen
    between private runs; the publishable claim is the run after the fixes, with the
    before/after both retained internally.

## 6. Run ledger

| Date | Run | Agent | Config | Outcome |
|------|-----|-------|--------|---------|
| 2026-09-02 | stub_smoke | rag_naive | stub LLM/judge, tfidf, medical_slice (2 ep / 56 ckpt) | pipeline mechanics verified |
| 2026-09-02 | rag_naive_slice_openai | rag_naive | paper config | FAILED — OpenAI account has no credits (credit_balance_exhausted) |
| 2026-09-02 | plur_stub_smoke | plur | stub LLM/judge, medical_slice | adapter integration verified: 224/225 turns stored, deletion path fired (1–3 deletion turns/ep, up to 8 engrams retired), 20 retrieved/ckpt, 0 errors |
| 2026-09-02 | cal_rag_naive_or / cal_plur_or | both | gpt-4o-mini answers + gpt-4o judge via OpenRouter (--api_base), rag=tfidf, medical_slice, PLUR CLI v0.16.1 | first real scores (n small): utility 0.10 vs 0.15; privacy answer leak 0.50 vs 0.61; **deletion answer leak 0.39 vs 0.17 (PLUR halves it)**; deletion context leak 0.94 vs 0.50; compliance-utility 0.031 vs 0.049. Cost $0.18 total → full-run projection ≈ $7.2 |
| 2026-09-02 | p2_* (8 runs) | plur + rag_naive(HF MiniLM embeddings) | full 4 domains, same models | Phase 2 base COMPLETE (~$11). PLUR MGS mean 13.9 vs baseline 12.5; wins 3/4 domains; top memory-method on Medical at this backbone (23.6 vs board's 21.6); F(ans) best in 4/4. Weak: household vs Mem0's 27.4; education mud for all. Full report: [[gatemem-phase2-report-2026-09-02]]. Two upstream notes: langchain retriever unpack bug (used native path); requirements.txt misses scikit-learn. Driver was externally stopped twice mid-run; user confirmed resume. |
| 2026-09-02 | p2b_plur_* (20 runs) | plur only | 5 board backbones (dsv4, gpt-5-mini, llama-4-maverick, gemini-2.5-flash-lite, gpt-5.4) × 4 domains, judge gpt-4o | Phase 2b board-comparison sweep — IN PROGRESS after user topped up OpenRouter (~$59 available, floor $8). Paper baselines serve as comparators per backbone. |
| 2026-09-23 | — | — | Phase 3 gate | **Owner approved submission** to the public leaderboard, conditional on a rerun on the latest release. Scope: the 12 cells the GateMem-Submit form lists (gpt-4o-mini, gpt-5-mini, gemini-2.5-flash-lite × 4 domains), conceded 4o-mini household included; method "PLUR", family External memory, contact dev@plur.ai; this repo made public as the artifact link. |
| 2026-09-23 | r3smoke_plur_4omini_medical_slice | plur | PLUR CLI + SDK **0.20.1** (was 0.16.1), harness unchanged at 603f9f4, gpt-4o-mini + gpt-4o judge | smoke: leakage identical to cal_plur_or (A 0.611, F 0.167), U 0.10 vs 0.15 (≈1 question at n=56). Apparent 3.6× slowdown was host load (load avg ~50); per-call benchmark equal across versions. |
| 2026-09-23 | r3_plur_* (12 runs) | plur only | 0.20.1, same models/flags as p2/p2b (12288 max output on sweep backbones), `scripts/run_rerun_latest.sh` + `with_retry.sh` | Pre-submission rerun. 9/12 done at 19:45; every finished cell within ±3 of its 0.16.1 MGS (largest move: g25fl office 24.5→21.9). Two DNS outages (openrouter.ai unresolvable) killed the driver; `with_retry.sh` now resumes automatically. Upload files built from r3 and verified with the official scorer (checkpoint join and rule metrics exact). |
| 2026-09-23 | r3smoke_plur_{opus55,astra6}_medical_slice | plur | anthropic/claude-opus-5.5, openai/gpt-6-astra via OpenRouter, 0.20.1 | frontier smokes: MGS 40.0 / 35.0 with A=0, F=0 on the slice (small n — not a claim). Cost per checkpoint 1.9¢ / 2.4¢ excluding judge. Full medical runs queued for both; other domains are an owner decision after medical. Not board backbones — showcase only. |
| 2026-09-24 | r3_plur_* (12) + r3_plur_{opus55,astra6}_medical | plur | 0.20.1 | Rerun complete. All 12 leaderboard cells PLUR #1 external-memory except 4o-mini household (Mem0). Outside ±3 vs 0.16.1: g5mini office 52.4→56.6, education 28.8→25.1, household 53.0→46.5 (single seed; a second household seed is recommended before quoting that cell). Frontier medical: Opus 5.5 MGS 57.8 (A 3.1, F 0.6), $11.28; GPT-Astra-6 MGS 47.1 (A 3.1, F 0.0), $15.95. Metric mapping re-verified against GateMem docs/evaluation_protocol.md. |
