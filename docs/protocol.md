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
