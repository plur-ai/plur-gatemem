#!/usr/bin/env python3
"""Generate a tamper-evident reproducibility manifest for the GateMem runs.

Captures per run: SHA-256 + row counts of every artifact and the declared
configuration; plus environment facts (GateMem harness commit + local diff,
PLUR CLI version, dataset hashes). Writes manifest.json at the repo root.

Usage: python3 scripts/gatemem_manifest.py [--harness /path/to/GateMem]
The default artifact source is this repo's outputs/ (gzipped); pass
--harness to also record the live harness environment and dataset hashes.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_CONFIG = {
    "harness_config": "configs/runs/paper_main.yaml",
    "answer_model": "openai/gpt-4o-mini",
    "judge_model": "openai/gpt-4o",
    "temperature": 0.2,
    "judge_temperature": 0.0,
    "top_k": 20,
    "answer_protocol": "standard",
    "serving": "OpenRouter (https://openrouter.ai/api/v1)",
    "serving_caveat": (
        "openai/* models are served by OpenAI via OpenRouter; deepseek/meta-llama/google "
        "models may be routed across multiple upstream providers by OpenRouter — provider "
        "not pinned, recorded as a reproducibility caveat."
    ),
}

FAMILY_CONFIG = {
    "p2_plur": {**BASE_CONFIG, "agent": "plur", "max_output_tokens": 4096,
                "retrieval": "PLUR product (BM25 + BGE hybrid via @plur-ai/cli)"},
    "p2_rag_naive": {**BASE_CONFIG, "agent": "rag_naive", "max_output_tokens": 4096,
                     "retrieval": "embedding (native), sentence-transformers/all-MiniLM-L6-v2"},
    "p2b_plur": {**BASE_CONFIG, "agent": "plur", "max_output_tokens": 12288,
                 "retrieval": "PLUR product (BM25 + BGE hybrid via @plur-ai/cli)"},
}

BACKBONE_TAGS = {
    "dsv4": "deepseek/deepseek-v4-pro",
    "g5mini": "openai/gpt-5-mini",
    "llmav": "meta-llama/llama-4-maverick",
    "g25fl": "google/gemini-2.5-flash-lite",
    "g54": "openai/gpt-5.4",
    "g56sol": "openai/gpt-5.6-sol",
}

# Honest exceptions discovered during execution.
RUN_NOTES = {
    "p2b_plur_dsv4_medical": "ran fully at max_output_tokens=4096 (before the cap raise)",
    "p2b_plur_dsv4_office": (
        "MIXED CAP: first ~520 checkpoints at max_output_tokens=4096, resumed remainder at "
        "12288 after a reasoning-token truncation crash (LLMError max_output_tokens)"
    ),
}


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def jsonl_rows(path: str) -> int:
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt") as f:  # type: ignore[operator]
        return sum(1 for _ in f)


def sh(cmd: list[str], cwd: str | None = None) -> str:
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception as e:  # pragma: no cover
        return f"<error: {e}>"


def run_config(run_name: str) -> dict:
    for fam in sorted(FAMILY_CONFIG, key=len, reverse=True):
        if run_name.startswith(fam):
            cfg = dict(FAMILY_CONFIG[fam])
            break
    else:
        return {"unknown_family": True}
    if run_name.startswith("p2b_plur_"):
        tag = run_name.split("_")[2]
        cfg["answer_model"] = BACKBONE_TAGS.get(tag, f"<unknown tag {tag}>")
    if run_name in RUN_NOTES:
        cfg["note"] = RUN_NOTES[run_name]
    return cfg


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", default="/Users/gregor/Data/5-plur/2-projects/GateMem")
    args = ap.parse_args()

    manifest: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "protocol": "docs/protocol.md",
        "environment": {
            "plur_cli_version": sh(["plur", "--version"]),
            "python": sys.version.split()[0],
            "metric_mapping": "official (GateMem docs/evaluation_protocol.md): U=utility_accuracy, "
                              "A=privacy_leakage_rate, F=deletion_leakage_rate, "
                              "MGS=compliance_utility_score",
        },
        "dataset_hashes": {},
        "runs": {},
    }

    if os.path.isdir(args.harness):
        manifest["environment"].update(
            {
                "gatemem_commit": sh(["git", "rev-parse", "HEAD"], cwd=args.harness),
                "gatemem_origin": sh(["git", "remote", "get-url", "origin"], cwd=args.harness),
                "gatemem_local_changes": sh(["git", "status", "--porcelain"], cwd=args.harness).splitlines(),
            }
        )
        for domain in ["medical", "office", "education", "household"]:
            for fname in ["episodes.jsonl", "checkpoints.jsonl"]:
                p = os.path.join(args.harness, "bench", "data", domain, fname)
                if os.path.exists(p):
                    manifest["dataset_hashes"][f"{domain}/{fname}"] = sha256(p)

    outputs = os.path.join(REPO, "outputs")
    for run_name in sorted(os.listdir(outputs)):
        rd = os.path.join(outputs, run_name)
        if not os.path.isdir(rd):
            continue
        entry: dict = {"config": run_config(run_name), "artifacts": {}}
        for fname in sorted(os.listdir(rd)):
            p = os.path.join(rd, fname)
            art = {"sha256": sha256(p), "bytes": os.path.getsize(p)}
            if ".jsonl" in fname:
                art["rows"] = jsonl_rows(p)
            entry["artifacts"][fname] = art
        entry["complete"] = "summary.json" in entry["artifacts"]
        manifest["runs"][run_name] = entry

    out = os.path.join(REPO, "manifest.json")
    with open(out, "w") as f:
        json.dump(manifest, f, indent=1)
    done = sum(1 for r in manifest["runs"].values() if r["complete"])
    print(f"manifest written: {out} — {len(manifest['runs'])} runs ({done} complete)")


if __name__ == "__main__":
    main()
