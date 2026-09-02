#!/usr/bin/env python3
"""Aggregate GateMem Phase 2 run summaries into a per-domain comparison table.

Usage: python3 gatemem_analyze.py [outputs_dir]
Reads outputs/p2_{agent}_{domain}/summary.json for agents (plur, rag_naive)
and domains (medical, office, education, household).

MGS mapping (verified against scorer output on the calibration slice):
  compliance_utility_score       = U * (1 - A_answer) * (1 - F_answer)
  compliance_utility_e2e_score   = U * (1 - A_e2e)    * (1 - F_e2e)
where U = utility_accuracy, A = privacy leakage, F = deletion leakage.
"""
from __future__ import annotations

import json
import os
import sys

AGENTS = ["plur", "rag_naive"]
DOMAINS = ["medical", "office", "education", "household"]
FIELDS = [
    ("utility_accuracy", "U"),
    ("privacy_answer_leakage_rate", "A(ans)"),
    ("deletion_answer_leakage_rate", "F(ans)"),
    ("privacy_e2e_leakage_rate", "A(e2e)"),
    ("deletion_e2e_leakage_rate", "F(e2e)"),
    ("over_refusal_rate", "over-refuse"),
    ("compliance_utility_score", "MGS(ans)"),
    ("compliance_utility_e2e_score", "MGS(e2e)"),
    ("n_checkpoints", "n"),
]


def load(outputs: str, agent: str, domain: str) -> dict | None:
    p = os.path.join(outputs, f"p2_{agent}_{domain}", "summary.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


def fmt(v) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.3f}"
    return str(v)


def main() -> None:
    outputs = sys.argv[1] if len(sys.argv) > 1 else "outputs"
    grand: dict[str, dict[str, list[float]]] = {a: {} for a in AGENTS}
    for domain in DOMAINS:
        print(f"\n=== {domain} ===")
        header = f"{'metric':<14}" + "".join(f"{a:>12}" for a in AGENTS)
        print(header)
        rows = {a: load(outputs, a, domain) for a in AGENTS}
        if all(r is None for r in rows.values()):
            print("  (no runs yet)")
            continue
        for key, label in FIELDS:
            line = f"{label:<14}"
            for a in AGENTS:
                v = (rows[a] or {}).get(key)
                line += f"{fmt(v):>12}"
                if isinstance(v, (int, float)) and key != "n_checkpoints":
                    grand[a].setdefault(key, []).append(float(v))
            print(line)

    print("\n=== unweighted mean across completed domains ===")
    print(f"{'metric':<14}" + "".join(f"{a:>12}" for a in AGENTS))
    for key, label in FIELDS:
        if key == "n_checkpoints":
            continue
        line = f"{label:<14}"
        for a in AGENTS:
            vals = grand[a].get(key, [])
            line += f"{(sum(vals)/len(vals)):>12.3f}" if vals else f"{'-':>12}"
        print(line)


if __name__ == "__main__":
    main()
