# plur-gatemem — private GateMem evaluation of PLUR

Private (pre-publication) evaluation of [PLUR](https://plur.ai) on the
[GateMem benchmark](https://github.com/rzhub/GateMem) (arXiv:2606.18829) —
memory governance for multi-principal shared-memory agents:
**MGS = U · (1−A) · (1−F)** (utility × access-control × active forgetting).

Nothing here is published or submitted until the Phase 3 gate is explicitly
approved (see `docs/protocol.md` §5).

## Layout

| Path | What |
|---|---|
| `agents/plur_agent.py` | Clean-room GateMem agent backed by the released `@plur-ai/cli` (drop into `bench/agents/` + registry entry — the only harness modifications) |
| `scripts/run_phase2.sh` | Run driver: base comparison (PLUR vs RAG-Naive, GPT-4o-mini) + `PHASE2B=1` backbone sweeps; OpenRouter balance floor guard |
| `scripts/gatemem_analyze.py` | Aggregates run summaries into per-domain comparison tables |
| `scripts/gatemem_manifest.py` | Regenerates `manifest.json` (SHA-256 of all artifacts, configs, environment) |
| `docs/protocol.md` | Binding clean-room / honesty protocol + run ledger |
| `docs/phase2-report.md` | Phase 2 base results report (GPT-4o-mini backbone) |
| `outputs/<run>/` | Raw artifacts per run: `summary.json`, gzipped `predictions` / `judge_scores` / `scores` |
| `manifest.json` | Tamper-evident manifest over everything above |

## Reproduce

1. Clone `rzhub/GateMem` (commit in `manifest.json`), install `requirements.txt`
   **plus `scikit-learn`** (missing upstream), create the venv.
2. `npm i -g @plur-ai/cli` (version in `manifest.json`), `pip install -e packages/python`
   from the PLUR monorepo (`plur_ai` SDK).
3. Copy `agents/plur_agent.py` into `bench/agents/`, register `"plur": PlurAgent`
   in `bench/agents/__init__.py`.
4. Run `scripts/run_phase2.sh` (base) / `PHASE2B=1 scripts/run_phase2.sh` (sweeps).
   Set `OPENROUTER_API_KEY`; models and flags are in the script.

Known upstream issues hit during this work: `rag_naive --embedding_impl langchain`
crashes on a 3-tuple unpack (use `native`); `requirements.txt` misses `scikit-learn`;
reasoning backbones need `--max_output_tokens` ≥ 12288 or responses truncate to empty.

## Status

- Phase 2 base and 2b backbone sweeps (PLUR 0.16.1): complete. See `docs/phase2-report.md` and `docs/board-comparison.md`.
- **Leaderboard submission (PLUR 0.20.1):** the `r3_plur_*` runs cover the three backbones the GateMem-Submit form lists (GPT-4o-mini, GPT-5-mini, Gemini-2.5-Flash-Lite) × 4 domains. The uploaded files are in `submission/`, built by `scripts/gatemem_build_submission.py` and sent by `scripts/gatemem_submit.py`.
- Frontier backbones (medical only, not on the leaderboard): `r3_plur_opus55_medical`, `r3_plur_astra6_medical`.
- Run ledger and honesty protocol: `docs/protocol.md`.
