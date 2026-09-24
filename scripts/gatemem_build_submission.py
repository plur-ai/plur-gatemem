"""Build GateMem leaderboard submission files from run outputs.

Writes submission/<run>/predictions.jsonl in the run_eval.py schema the
GateMem-Submit Space accepts, keeping only the fields the evaluator reads
(checkpoint_id + output.{action, answer, answer_structured, used_record_ids}).

Usage: python3 gatemem_build_submission.py <run> [<run> ...]
"""
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEEP = ("action", "answer", "answer_structured", "used_record_ids")


def build(run: str) -> Path:
    src = ROOT / "outputs" / run / "predictions.jsonl.gz"
    dst = ROOT / "submission" / run / "predictions.jsonl"
    dst.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with gzip.open(src, "rt") as fin, dst.open("w") as fout:
        for line in fin:
            rec = json.loads(line)
            out = rec["output"]
            slim = {"checkpoint_id": rec["checkpoint_id"],
                    "output": {k: out.get(k, {} if k == "answer_structured" else [] if k == "used_record_ids" else "") for k in KEEP}}
            fout.write(json.dumps(slim, ensure_ascii=False) + "\n")
            n += 1
    print(f"{run}: {n} predictions -> {dst.relative_to(ROOT)}")
    return dst


if __name__ == "__main__":
    for r in sys.argv[1:]:
        build(r)
