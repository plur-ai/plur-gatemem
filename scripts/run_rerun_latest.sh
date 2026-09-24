#!/bin/bash
# GateMem pre-submission rerun — PLUR (v1 adapter) on the latest release, for the
# three backbones the GateMem-Submit form lists, all 4 domains. Same models, judge
# and flags as run_phase2.sh; only the PLUR version changes. Run names carry the
# version tag so the 0.16.1 results stay intact for before/after comparison.
#
# Env: GATEMEM_REPO (harness checkout), OPENROUTER_API_KEY, PLUR_CLI (pinned binary),
#      TAG (run-name prefix, e.g. r3), SMOKE=1 runs medical_slice @ gpt-4o-mini only.
# Guardrail: aborts below the $8 OpenRouter floor (shared with the fleet's crons).
set -euo pipefail

REPO=${GATEMEM_REPO:?set GATEMEM_REPO to your rzhub/GateMem checkout}
: "${OPENROUTER_API_KEY:?set OPENROUTER_API_KEY}"
: "${PLUR_CLI:?set PLUR_CLI to the pinned plur binary}"
TAG=${TAG:-r3}
FLOOR=8.0
cd "$REPO"
export PLUR_CLI

echo "[rerun] plur $("$PLUR_CLI" --version) · sdk $(.venv/bin/python -c 'import importlib.metadata as m; print(m.version("plur-ai"))')"

balance() {
  curl -s -m 15 -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/credits \
    | python3 -c "import json,sys; d=json.load(sys.stdin)['data']; print(round(d['total_credits']-d['total_usage'],2))"
}

check_floor() {
  B=$(balance)
  echo "[rerun] balance: \$$B"
  python3 -c "import sys; sys.exit(0 if float('$B') >= float('$FLOOR') else 1)" \
    || { echo "[rerun] ABORT: balance \$$B below floor \$$FLOOR — rerun after top-up (completed runs are skipped)"; exit 2; }
}

run_one() {
  local model=$1 tag=$2 domain=$3 extra=${4:-}
  local run_name="${TAG}_plur_${tag}_${domain}"
  if [ -f "outputs/${run_name}/summary.json" ]; then
    echo "[rerun] skip ${run_name} (summary exists)"; return 0
  fi
  check_floor
  echo "[rerun] === plur / ${model} / ${domain} ==="
  # shellcheck disable=SC2086
  .venv/bin/python bench/scripts/run_eval.py \
    --config configs/runs/paper_main.yaml \
    --data_dir "bench/data/${domain}" \
    --agent plur \
    --api_base https://openrouter.ai/api/v1 --api_key_env OPENROUTER_API_KEY \
    --llm_provider openai --llm_model "$model" \
    --judge_provider openai --judge_model openai/gpt-4o \
    --episode_concurrency 2 --judge_concurrency 3 $extra \
    --resume --run_name "$run_name" 2>&1 | tail -3
}

if [ "${SMOKE:-0}" = "1" ]; then
  TAG="${TAG}smoke"
  run_one openai/gpt-4o-mini 4omini medical_slice
  exit 0
fi

# Cheapest first, so a floor stop leaves the most cells complete.
for pair in "openai/gpt-4o-mini 4omini" "google/gemini-2.5-flash-lite g25fl" "openai/gpt-5-mini g5mini"; do
  model=${pair%% *}; tag=${pair##* }
  extra=""
  # p2 base (4o-mini) ran without it; every p2b sweep backbone ran with it.
  [ "$tag" != "4omini" ] && extra="--max_output_tokens 12288"
  for domain in medical office education household; do
    run_one "$model" "$tag" "$domain" "$extra"
  done
  echo "[rerun] balance after ${model}: \$$(balance)"
done
echo "[rerun] DONE"
