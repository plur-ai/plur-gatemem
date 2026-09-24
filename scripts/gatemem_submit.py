"""Submit PLUR's GateMem cells to the public leaderboard (GateMem-Submit Space).

Dry run by default: prints the submissions it would make and checks every file.
Pass --submit to actually send them. Submitting is the Phase 3 gate in
docs/protocol.md §5 — it needs explicit owner approval first.

Requires gradio_client (pip install gradio_client) — kept out of the harness venv.

Usage: python3 gatemem_submit.py --code-url URL [--tag r3] [--submit]
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPACE = "Ray368/GateMem-Submit"
BACKBONES = {"4omini": "GPT-4o-mini", "g5mini": "GPT-5-mini", "g25fl": "Gemini-2.5-Flash-Lite"}
DOMAINS = {"medical": "Medical", "office": "Office", "education": "Education", "household": "Household"}
EXPECTED = {"medical": 579, "office": 547, "education": 540, "household": 552}


def plan(tag: str) -> list[dict]:
    rows = []
    for bt, backbone in BACKBONES.items():
        for d, domain in DOMAINS.items():
            run = f"{tag}_plur_{bt}_{d}"
            f = ROOT / "submission" / run / "predictions.jsonl"
            n = sum(1 for _ in f.open()) if f.exists() else 0
            rows.append({"run": run, "file": f, "backbone": backbone, "domain": domain,
                         "n": n, "ok": n == EXPECTED[d]})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="r3")
    ap.add_argument("--method", default="PLUR")
    ap.add_argument("--contact", default="dev@plur.ai")
    ap.add_argument("--code-url", required=True)
    ap.add_argument("--submit", action="store_true")
    args = ap.parse_args()

    rows = plan(args.tag)
    for r in rows:
        print(f"{'ok ' if r['ok'] else 'BAD'} {r['run']:<26} {r['backbone']:<22} {r['domain']:<10} {r['n']} checkpoints")
    bad = [r for r in rows if not r["ok"]]
    if bad:
        raise SystemExit(f"{len(bad)} cell(s) missing or incomplete — build them with gatemem_build_submission.py first")
    if not args.submit:
        print(f"\nDry run: {len(rows)} submissions to {SPACE} as '{args.method}' (External memory), "
              f"contact {args.contact}, code {args.code_url}, LLM judge on. Pass --submit to send.")
        return

    from gradio_client import Client, handle_file
    client = Client(SPACE, verbose=False)
    log = ROOT / "submission" / f"{args.tag}_submitted.jsonl"
    with log.open("a") as out:
        for r in rows:
            status = client.predict(handle_file(str(r["file"])), args.method, r["backbone"], r["domain"],
                                    "External memory", args.contact, args.code_url, True,
                                    api_name="/submit_result")
            print(f"{r['run']}: {status}")
            out.write(json.dumps({"run": r["run"], "backbone": r["backbone"], "domain": r["domain"],
                                  "status": status}) + "\n")


if __name__ == "__main__":
    main()
