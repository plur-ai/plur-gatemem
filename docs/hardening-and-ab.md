# Hardening set + v2 A/B — results and decisions (2026-09-04)

Purpose: close the environment-uplift confound before any public claim, and test two
candidate adapter improvements. Protocol: docs/protocol.md. All runs in manifest.json.

## 1. Hardening: baselines head-to-head in OUR environment

| Run | Method | Backbone / domain | U | A | F | MGS |
|---|---|---|---|---|---|---|
| h_amem_dsv4_medical | A-Mem | deepseek / medical | 69.0 | 22.4 | 11.3 | **47.5** |
| p2b_plur_dsv4_medical (seed 1) | PLUR | deepseek / medical | 65.7 | 19.8 | 9.6 | 47.6 |
| h_plur_dsv4_medical_seed2 | PLUR | deepseek / medical | 68.6 | 14.6 | 9.0 | **53.3** |
| h_amem_g54_medical | A-Mem | gpt-5.4 / medical | 61.9 | 23.4 | 5.1 | **45.0** |
| p2b_plur_g54_medical | PLUR | gpt-5.4 / medical | 71.0 | 21.9 | 10.2 | **49.8** |

**Findings:**
- **Environment uplift is measured and small**: A-Mem head-to-head scored 47.5 vs its
  published 45.9 (deepseek medical) → ~+1.6. The uplift does not explain PLUR's leads.
- **Seed variance is real**: PLUR deepseek medical 47.6 / 53.3 across two seeds (±3
  around a 50.5 mean). Public claims must not lean on sub-3-point margins.
- **Head-to-head verdicts**: deepseek medical — PLUR two-seed mean 50.5 vs A-Mem 47.5
  (leads; single seeds within noise). gpt-5.4 medical — PLUR 49.8 vs A-Mem 45.0
  (clean lead, same environment).
- **h_mem0_4omini_household is INVALID**: U 0.0, over-refusal 100% — the mem0 upstream
  pipeline produced no usable memories in this environment. Excluded from all claims;
  Mem0's published household 27.4 remains the honest comparator (and remains above our
  15.0 there).

## 2. v2 adapter A/B (gpt-4o-mini, vs v1 p2 baselines)

| Variant | Domain | U | A | F | MGS | v1 MGS | Verdict |
|---|---|---|---|---|---|---|---|
| extract-at-ingest | medical | 43.3 | 55.2 | 20.9 | 15.4 | 23.6 | **NEGATIVE** |
| extract-at-ingest | household | 13.6 | 15.8 | 10.3 | 10.3 | 15.0 | **NEGATIVE** |
| deletion-widening (topk 2) | medical | 54.3 | 49.5 | 13.0 | 23.9 | 23.6 | noise (+0.3, within ±3 seed var) |

**Findings:**
- **Extraction with a mini-model extractor destroys answerable detail** — U dropped in
  both domains, over-refusal rose. The hypothesis (Mem0-style ingest extraction as a
  cheap utility win) is falsified at this extractor strength. A stronger extractor is
  untested and no longer low-hanging.
- **Semantic deletion-widening is safe but unproven** — +0.3 MGS is inside measured seed
  variance. Not adopted for the submission config.

## 3. Decisions

1. **Submission config = v1 adapter, unchanged** (the config behind all p2/p2b runs).
2. v2 variants stay in the repo as documented negative results (env-gated, off by default).
3. Claim language for Phase 3: "leads the external-memory class" backed by head-to-head
   runs and two-seed means; no decimal-point rank claims on cells closer than 3 points;
   household @4o-mini conceded to Mem0's published number.
