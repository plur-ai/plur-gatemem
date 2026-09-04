from __future__ import annotations

"""GateMem agent backed by PLUR (https://plur.ai) — the released product surface.

Clean-room notes (see 5-plur/1-tracks/research/gatemem-evaluation-protocol.md):
- Reads only harness-visible turn/checkpoint fields; never touches judge_spec,
  leak_targets, expected_action, attack_type, or episode `records` annotations.
- All memory operations go through the released `@plur-ai/cli` via the
  `plur_ai` Python SDK: learn / recall_hybrid / forget. No direct store writes.
- Every episode runs against a fresh throwaway store (PLUR_PATH override);
  the user's real ~/.plur is never touched.
- Deletion requests are natural language inside turns. Handling them is part of
  the system under test: heuristic intent detection -> extract target values ->
  recall -> forget by exact engram id. Deletion-request turns are never stored
  (they contain the very values being deleted).
"""

import logging
import os
import re
import shutil
import tempfile
import time
from typing import Any, Dict, List, Optional

from .base import BaseMemoryAgent, Checkpoint, Turn

try:
    from plur_ai import Plur
    from plur_ai.bridge import run_json as plur_run_json
except ImportError as _e:  # pragma: no cover
    Plur = None  # type: ignore[assignment]
    plur_run_json = None  # type: ignore[assignment]
    _PLUR_IMPORT_ERROR = _e
else:
    _PLUR_IMPORT_ERROR = None


# Imperative deletion-intent triggers. Deliberately conservative: fires on
# requests to delete/remove/erase/forget stored information, not on every
# mention of the word (turn_kind gating below narrows it further).
_DELETION_TRIGGER = re.compile(
    r"\b(please\s+)?(delete|erase|remove|scrub|purge|forget)\b[^.]{0,120}?"
    r"\b(memory|memories|record|records|note|notes|number|numbers|contact|contacts|"
    r"information|info|details|entry|entries|name|address|state|wording|history)\b",
    re.IGNORECASE,
)

# Value extractors for deletion targets: phone-like numbers, quoted spans,
# and Capitalized multi-word proper phrases.
_PHONE_RE = re.compile(r"\b\d{3}[-.\s]\d{3,4}[-.\s]\d{4}\b|\b\d{3}[-.\s]\d{4}\b")
_QUOTED_RE = re.compile(r"[\"“']([^\"”']{4,80})[\"”']")
_PROPER_RE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4})\b")

# Common sentence-initial words that produce false "proper phrase" hits.
_PROPER_STOPWORDS = {
    "The", "This", "That", "Please", "After", "Before", "Once", "Now", "Then",
    "Delete", "Remove", "Erase", "Forget", "Also", "And", "But", "When", "While",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
}


class PlurAgent(BaseMemoryAgent):
    """Memory agent backed by a per-episode PLUR store via the released CLI."""

    def __init__(
        self,
        *,
        top_k: int = 20,
        llm_mode: str = "leaky",
        llm_router: Any = None,
        query_prompt_path: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        plur_binary: Optional[str] = None,
        plur_store_root: Optional[str] = None,
        plur_call_timeout: float = 90.0,
        deletion_mode: str = "heuristic",  # heuristic|off
    ) -> None:
        if Plur is None:  # pragma: no cover
            raise RuntimeError(f"plur_ai SDK not importable: {_PLUR_IMPORT_ERROR}")
        super().__init__(
            top_k=top_k,
            llm_mode=llm_mode,
            llm_router=llm_router,
            query_prompt_path=query_prompt_path,
            logger=logger,
        )
        self.plur_binary = plur_binary or os.environ.get("PLUR_CLI") or None
        self.plur_store_root = plur_store_root or os.path.join(
            tempfile.gettempdir(), "gatemem_plur_stores"
        )
        self.plur_call_timeout = plur_call_timeout
        if deletion_mode not in {"heuristic", "off"}:
            raise ValueError("deletion_mode must be heuristic|off")
        self.deletion_mode = deletion_mode

        self.plur: Optional[Any] = None
        self.store_dir: Optional[str] = None
        self._counters: Dict[str, int] = {}
        self._forget_log: List[Dict[str, Any]] = []

        # ---- v2 options (env-gated; defaults reproduce v1 exactly) ----
        # PLUR_INGEST_MODE=extract  -> distill turn windows into atomic facts
        #   via the run's answer LLM before plur.learn (mirrors real PLUR
        #   usage, where the agent distills before learning).
        # PLUR_DELETION_SEMANTIC_TOPK=N -> additionally retire the top-N
        #   hybrid-recall near-matches per deletion target (paraphrase
        #   residue that lexical matching misses). 0 disables (v1).
        self.ingest_mode = os.environ.get("PLUR_INGEST_MODE", "raw").strip().lower()
        if self.ingest_mode not in {"raw", "extract"}:
            raise ValueError("PLUR_INGEST_MODE must be raw|extract")
        try:
            self.deletion_semantic_topk = int(os.environ.get("PLUR_DELETION_SEMANTIC_TOPK", "0"))
        except ValueError:
            self.deletion_semantic_topk = 0
        self._extract_window = int(os.environ.get("PLUR_EXTRACT_WINDOW", "8"))
        self._turn_buffer: List[Turn] = []

    # ------------------------------------------------------------------ reset

    def reset(self, episode: Dict[str, Any]) -> None:
        super().reset(episode)
        episode_id = str((episode or {}).get("episode_id") or "ep")
        safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", episode_id)[:80]
        os.makedirs(self.plur_store_root, exist_ok=True)
        # Fresh store per episode; a stale dir from a crashed run is removed.
        self.store_dir = os.path.join(self.plur_store_root, f"{safe_id}_{int(time.time())}")
        if os.path.exists(self.store_dir):  # pragma: no cover
            shutil.rmtree(self.store_dir, ignore_errors=True)
        os.makedirs(self.store_dir, exist_ok=True)
        self.plur = Plur(path=self.store_dir, binary=self.plur_binary, timeout=self.plur_call_timeout)
        self._counters = {
            "turns_seen": 0,
            "engrams_written": 0,
            "learn_errors": 0,
            "deletion_turns": 0,
            "engrams_forgotten": 0,
            "forget_errors": 0,
            "recall_errors": 0,
            "extraction_calls": 0,
            "extraction_fallbacks": 0,
            "semantic_forgets": 0,
        }
        self._forget_log = []
        self._turn_buffer = []

    # ----------------------------------------------------------------- ingest

    def ingest(self, turn: Turn) -> None:
        self._counters["turns_seen"] += 1
        text = (turn.text or "").strip()
        if not text:
            return

        if self.deletion_mode == "heuristic" and self._is_deletion_request(turn):
            # Flush pending extraction first so deletion targets exist as
            # engrams before we try to retire them.
            self._flush_extract_buffer()
            self._counters["deletion_turns"] += 1
            self._handle_deletion(turn)
            # Deletion-request turns are never stored: they contain the very
            # values being deleted, and storing them would defeat retirement.
            return

        if self.ingest_mode == "extract" and self.llm_router is not None:
            self._turn_buffer.append(turn)
            if len(self._turn_buffer) >= self._extract_window:
                self._flush_extract_buffer()
            return

        self._learn_raw_turn(turn)

    def _learn_raw_turn(self, turn: Turn) -> None:
        text = (turn.text or "").strip()
        speaker = f"{turn.speaker_principal_id} ({turn.speaker_role})"
        stamp = f"[{turn.timestamp}] " if turn.timestamp else ""
        statement = f"{stamp}{speaker}: {text}"
        tags = [
            f"principal:{turn.speaker_principal_id}",
            f"role:{turn.speaker_role}",
            f"turn:{turn.turn_id}",
        ]
        try:
            self.plur.learn(statement, type="procedural", tags=tags, source=turn.turn_id)
            self._counters["engrams_written"] += 1
        except Exception as e:
            self._counters["learn_errors"] += 1
            self.logger.warning("plur learn failed on %s: %s", turn.turn_id, e)

    # ------------------------------------------------------- v2: extraction

    _EXTRACT_SYSTEM = (
        "You distill dialogue into atomic memory facts for an assistant's "
        "long-term store. From the window of turns, extract every "
        "self-contained factual statement worth remembering: facts, "
        "preferences, contact details, schedules, policies, identifiers, "
        "instructions, and status changes. Each fact must name who said it "
        "(principal id and role) and stand alone without the window. Keep "
        "concrete values (names, numbers, dates) verbatim. Skip greetings "
        "and filler. Output STRICT JSON: an array of objects with keys "
        '"fact" (string) and "turn_id" (the source turn id). No other text.'
    )

    def _flush_extract_buffer(self) -> None:
        if not self._turn_buffer:
            return
        window = self._turn_buffer
        self._turn_buffer = []
        lines = []
        for t in window:
            stamp = f"[{t.timestamp}] " if t.timestamp else ""
            lines.append(f"{t.turn_id} {stamp}{t.speaker_principal_id} ({t.speaker_role}): {t.text}")
        user_prompt = "Turns:\n" + "\n".join(lines)
        facts: List[Dict[str, Any]] = []
        try:
            self._counters["extraction_calls"] += 1
            out = self.llm_router.complete(
                system_prompt=self._EXTRACT_SYSTEM, user_prompt=user_prompt
            )
            start, end = out.find("["), out.rfind("]")
            if start >= 0 and end > start:
                import json as _json

                parsed = _json.loads(out[start : end + 1])
                facts = [f for f in parsed if isinstance(f, dict) and f.get("fact")]
        except Exception as e:
            self.logger.warning("extraction failed, falling back to raw turns: %s", e)
        if not facts:
            # Honest fallback: never silently drop content on extractor failure.
            self._counters["extraction_fallbacks"] += 1
            for t in window:
                self._learn_raw_turn(t)
            return
        by_id = {t.turn_id: t for t in window}
        for f in facts:
            src = by_id.get(str(f.get("turn_id")))
            tags = [f"turn:{f.get('turn_id')}"]
            if src is not None:
                tags += [f"principal:{src.speaker_principal_id}", f"role:{src.speaker_role}"]
            try:
                self.plur.learn(str(f["fact"]), type="procedural", tags=tags,
                                source=str(f.get("turn_id") or ""))
                self._counters["engrams_written"] += 1
            except Exception as e:
                self._counters["learn_errors"] += 1
                self.logger.warning("plur learn (fact) failed: %s", e)

    # --------------------------------------------------------------- deletion

    @staticmethod
    def _is_deletion_request(turn: Turn) -> bool:
        return bool(_DELETION_TRIGGER.search(turn.text or ""))

    def _extract_deletion_targets(self, text: str) -> List[str]:
        targets: List[str] = []
        targets.extend(_PHONE_RE.findall(text))
        targets.extend(m.strip() for m in _QUOTED_RE.findall(text))
        for m in _PROPER_RE.findall(text):
            first = m.split()[0]
            if first not in _PROPER_STOPWORDS:
                targets.append(m.strip())
        # Dedup, keep order, cap to a sane number.
        seen: set[str] = set()
        out: List[str] = []
        for t in targets:
            tl = t.lower()
            if tl not in seen:
                seen.add(tl)
                out.append(t)
        return out[:12]

    def _handle_deletion(self, turn: Turn) -> None:
        text = turn.text or ""
        targets = self._extract_deletion_targets(text)
        candidate_ids: Dict[str, str] = {}  # id -> matched target
        queries = targets if targets else [text[:200]]
        for q in queries:
            try:
                hits = self.plur.recall(q, limit=10)
            except Exception as e:
                self._counters["recall_errors"] += 1
                self.logger.warning("plur recall (deletion) failed: %s", e)
                continue
            for h in hits or []:
                hid = h.get("id")
                stmt = (h.get("statement") or "")
                if not hid or hid in candidate_ids:
                    continue
                if targets:
                    # Conservative: retire only engrams that literally contain
                    # an extracted target value.
                    if any(t.lower() in stmt.lower() for t in targets):
                        candidate_ids[hid] = q
                else:
                    # No extractable values: retire only the top lexical hit.
                    candidate_ids[hid] = "topical"
                    break
        # v2: semantic widening — paraphrases of deleted facts survive lexical
        # matching; retire the top-K hybrid near-matches per target as well.
        if self.deletion_semantic_topk > 0 and targets:
            for q in targets:
                try:
                    sem = self.plur.recall_hybrid(q, limit=self.deletion_semantic_topk) or []
                except Exception as e:
                    self._counters["recall_errors"] += 1
                    self.logger.warning("plur recall_hybrid (deletion) failed: %s", e)
                    continue
                for h in sem[: self.deletion_semantic_topk]:
                    hid = h.get("id")
                    if hid and hid not in candidate_ids:
                        candidate_ids[hid] = f"semantic:{q[:40]}"
                        self._counters["semantic_forgets"] += 1

        for hid, matched in candidate_ids.items():
            try:
                plur_run_json(
                    ["forget", hid, "--reason", f"deletion request {turn.turn_id}"],
                    binary=self.plur_binary,
                    path=self.store_dir,
                    timeout=self.plur_call_timeout,
                )
                self._counters["engrams_forgotten"] += 1
                self._forget_log.append(
                    {"turn_id": turn.turn_id, "engram_id": hid, "matched": matched}
                )
            except Exception as e:
                self._counters["forget_errors"] += 1
                self.logger.warning("plur forget %s failed: %s", hid, e)

    # ------------------------------------------------------------------ query

    def query(self, checkpoint: Checkpoint) -> Dict[str, Any]:
        # Extraction mode buffers turns; a checkpoint may fire mid-window.
        self._flush_extract_buffer()
        retrieved: List[Dict[str, Any]] = []
        try:
            hits = self.plur.recall_hybrid(checkpoint.query_text, limit=self.top_k) or []
        except Exception as e:
            self._counters["recall_errors"] += 1
            self.logger.warning("plur recall_hybrid failed on %s: %s", checkpoint.checkpoint_id, e)
            hits = []

        for h in hits:
            stmt = h.get("statement") or ""
            # Speaker prefix was embedded at ingest: "[ts] principal (role): text"
            m = re.match(r"^(?:\[[^\]]*\]\s*)?([^:()]+?)\s*\(([^)]*)\):\s*", stmt)
            retrieved.append(
                {
                    "text": stmt,
                    "principal_id": (m.group(1).strip() if m else None),
                    "role": (m.group(2).strip() if m else None),
                    "record_refs": self._merge_record_refs(None, stmt),
                    "score": h.get("score") or h.get("relevance"),
                    "engram_id": h.get("id"),
                }
            )

        out = self._run_llm(checkpoint=checkpoint, retrieved_memory=retrieved)
        dbg = out.setdefault("debug", {})
        dbg["agent"] = "plur"
        dbg["counters"] = dict(self._counters)
        dbg["n_retrieved"] = len(retrieved)
        dbg["v2_config"] = {
            "ingest_mode": self.ingest_mode,
            "deletion_semantic_topk": self.deletion_semantic_topk,
            "extract_window": self._extract_window,
        }
        return out
