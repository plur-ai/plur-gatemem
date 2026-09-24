#!/bin/bash
# Run a GateMem driver, retrying transient failures (DNS, network, provider errors).
# Every driver runs with --resume, so a retry continues where the failed run stopped.
# Exit 2 (balance floor) is not retried: it needs a top-up, not another attempt.
#
# Usage: with_retry.sh <max-attempts> <command> [args...]
set -uo pipefail

MAX=${1:?max attempts}; shift
for attempt in $(seq 1 "$MAX"); do
  "$@"; rc=$?
  [ "$rc" -eq 0 ] && exit 0
  [ "$rc" -eq 2 ] && { echo "[retry] floor abort — not retrying"; exit 2; }
  echo "[retry] attempt $attempt/$MAX exited $rc at $(date +%H:%M); retrying in 120s"
  sleep 120
done
echo "[retry] giving up after $MAX attempts"
exit 1
