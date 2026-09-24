#!/bin/bash
# GateMem smoke test for one backbone: PLUR (v1 adapter) on a single domain,
# medical_slice by default. Use it before a full run of a new backbone to confirm
# the harness works with the model and to measure cost per checkpoint.
#
# Usage: run_smoke_model.sh <openrouter-model-id> <tag> [domain]
# Env:   GATEMEM_REPO, OPENROUTER_API_KEY, PLUR_CLI, TAG (run-name prefix, default r3)
# Guardrail: aborts below the $8 OpenRouter floor (shared with the fleet's crons).
set -euo pipefail

MODEL=${1:?model id}; MTAG=${2:?short tag}; DOMAIN=${3:-medical_slice}
REPO=${GATEMEM_REPO:?set GATEMEM_REPO to your rzhub/GateMem checkout}
: "${OPENROUTER_API_KEY:?set OPENROUTER_API_KEY}"
: "${PLUR_CLI:?set PLUR_CLI to the pinned plur binary}"
TAG=${TAG:-r3}
FLOOR=8.0
cd "$REPO"
export PLUR_CLI

balance() {
  curl -s -m 15 -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/credits \
    | python3 -c "import json,sys; d=json.load(sys.stdin)['data']; print(round(d['total_credits']-d['total_usage'],2))"
}

B0=$(balance)
python3 -c "import sys; sys.exit(0 if float('$B0') >= float('$FLOOR') else 1)" \
  || { echo "[smoke] ABORT: balance \$$B0 below floor \$$FLOOR"; exit 2; }
# Slice runs are smoke tests; a full domain gets a normal run name.
case "$DOMAIN" in *_slice) RUN="${TAG}smoke_plur_${MTAG}_${DOMAIN}" ;; *) RUN="${TAG}_plur_${MTAG}_${DOMAIN}" ;; esac
echo "[smoke] plur $("$PLUR_CLI" --version) · ${MODEL} · ${DOMAIN} · balance \$$B0"
.venv/bin/python bench/scripts/run_eval.py \
  --config configs/runs/paper_main.yaml \
  --data_dir "bench/data/${DOMAIN}" \
  --agent plur \
  --api_base https://openrouter.ai/api/v1 --api_key_env OPENROUTER_API_KEY \
  --llm_provider openai --llm_model "$MODEL" \
  --judge_provider openai --judge_model openai/gpt-4o \
  --max_output_tokens 12288 \
  --episode_concurrency 2 --judge_concurrency 3 \
  --resume --run_name "$RUN" 2>&1 | tail -3
B1=$(balance)
N=$(wc -l < "outputs/${RUN}/predictions.jsonl")
echo "[smoke] ${RUN}: ${N} checkpoints, cost \$$(python3 -c "print(round($B0-$B1,2))") (balance is shared, so concurrent runs inflate this)"
