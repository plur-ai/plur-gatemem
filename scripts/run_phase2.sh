#!/bin/bash
# GateMem Phase 2 private run driver — PLUR vs rag_naive across all 4 domains.
# Protocol: 5-plur/1-tracks/research/gatemem-evaluation-protocol.md
# Guardrail: aborts if the shared OpenRouter balance would drop below $8
# (Winston's crons run on this account — never starve the fleet).
set -euo pipefail

REPO=${GATEMEM_REPO:?set GATEMEM_REPO to your rzhub/GateMem checkout}
FLOOR=8.0
cd "$REPO"

: "${OPENROUTER_API_KEY:?set OPENROUTER_API_KEY}"

balance() {
  curl -s -m 15 -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/credits \
    | python3 -c "import json,sys; d=json.load(sys.stdin)['data']; print(round(d['total_credits']-d['total_usage'],2))"
}

check_floor() {
  B=$(balance)
  echo "[phase2] balance: \$$B"
  python3 -c "import sys; sys.exit(0 if float('$B') >= float('$FLOOR') else 1)" \
    || { echo "[phase2] ABORT: balance \$$B below floor \$$FLOOR — resume with --resume after top-up"; exit 2; }
}

run_one() {
  local domain=$1 agent=$2 extra=$3
  local run_name="p2_${agent}_${domain}"
  if [ -f "outputs/${run_name}/summary.json" ]; then
    echo "[phase2] skip ${run_name} (summary exists)"
    return 0
  fi
  check_floor
  echo "[phase2] === $agent / $domain ==="
  # shellcheck disable=SC2086
  .venv/bin/python bench/scripts/run_eval.py \
    --config configs/runs/paper_main.yaml \
    --data_dir "bench/data/${domain}" \
    --agent "$agent" $extra \
    --api_base https://openrouter.ai/api/v1 --api_key_env OPENROUTER_API_KEY \
    --llm_provider openai --llm_model openai/gpt-4o-mini \
    --judge_provider openai --judge_model "${JUDGE_MODEL:-openai/gpt-4o}" \
    --episode_concurrency 2 --judge_concurrency 3 \
    --resume --run_name "$run_name" 2>&1 | tail -4
}

# rag_naive uses local HF embeddings (free) — closest free stand-in for the
# paper's embedding-retrieval baseline; recorded as a config deviation.
RAG_EXTRA="--retrieval_backend embedding --embedding_impl native --embed_provider hf --embed_model sentence-transformers/all-MiniLM-L6-v2"

for domain in medical office education household; do
  run_one "$domain" plur ""
  run_one "$domain" rag_naive "$RAG_EXTRA"
done

echo "[phase2] final balance: \$$(balance)"
echo "[phase2] DONE"

# ---------------------------------------------------------------------------
# Phase 2b — PLUR-only backbone sweeps for board comparison (paper baselines
# already exist per backbone on the official ledger, so only PLUR needs runs).
# Invoke:  PHASE2B=1 gatemem-run-phase2.sh   (after base phase 2 is complete)
# Judge stays openai/gpt-4o for every sweep (paper judge).
# ---------------------------------------------------------------------------
if [ "${PHASE2B:-0}" = "1" ]; then
  BACKBONES=(
    "deepseek/deepseek-v4-pro dsv4"
    "openai/gpt-5-mini g5mini"
    "meta-llama/llama-4-maverick llmav"
    "google/gemini-2.5-flash-lite g25fl"
    "openai/gpt-5.4 g54"
    "openai/gpt-5.6-sol g56sol"
  )
  for pair in "${BACKBONES[@]}"; do
    model=${pair%% *}; tag=${pair##* }
    for domain in medical office education household; do
      run_name="p2b_plur_${tag}_${domain}"
      if [ -f "outputs/${run_name}/summary.json" ]; then
        echo "[phase2b] skip ${run_name}"; continue
      fi
      check_floor
      echo "[phase2b] === plur / ${model} / ${domain} ==="
      .venv/bin/python bench/scripts/run_eval.py \
        --config configs/runs/paper_main.yaml \
        --data_dir "bench/data/${domain}" \
        --agent plur \
        --api_base https://openrouter.ai/api/v1 --api_key_env OPENROUTER_API_KEY \
        --llm_provider openai --llm_model "$model" \
        --judge_provider openai --judge_model openai/gpt-4o \
        --max_output_tokens 12288 \
        --episode_concurrency 2 --judge_concurrency 3 \
        --resume --run_name "$run_name" 2>&1 | tail -3
    done
    echo "[phase2b] balance after ${model}: \$$(balance)"
  done
  echo "[phase2b] DONE"
fi
