#!/usr/bin/env python3
"""Deterministic memory-housekeeping: classify ALL pending auto_capture facts
via direct 9Router LLM API calls (no agent session, no tool calls).

Flow:
  1. Deterministic junk removal (tag-based test/dummy/probe).
  2. Repeatedly pick the OLDEST `--batch-size` un-reviewed auto_capture/entity:cron
     facts, classify via /v1/chat/completions (model default `free-burst`),
     apply verdicts — until pending is 0 or `--max` (total cap) is hit.
  3. Rebuild HRR vectors / VACUUM only if needed. Print a compact report;
     print nothing when there was nothing to do (cron stays silent).

Why direct-API: an agent session (LLM + tool-call loop) blows the output-length
limit when a capture burst dumps 100+ candidates into the prompt. Mini-batches
+ single JSON verdicts keep script stdout and LLM I/O bounded.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request

AGENT_HOME = os.environ.get("HERMES_AGENT", "/home/sonpham/.hermes/hermes-agent")
if AGENT_HOME not in sys.path:
    sys.path.insert(0, AGENT_HOME)

from plugins.memory import load_memory_provider  # noqa: E402

CONFIG_YAML = os.path.expanduser("~/.hermes/config.yaml")


def load_ninerouter_creds() -> tuple[str, str]:
    """Read base_url + api_key from the Hermes model config (custom provider)."""
    base_url = os.environ.get("NINEROUTER_URL", "http://localhost:20128/v1")
    api_key = os.environ.get("NINEROUTER_KEY", "")
    if not api_key and os.path.exists(CONFIG_YAML):
        text = open(CONFIG_YAML, encoding="utf-8").read()
        m = re.search(r"^model:\s*\n\s*api_key:\s*(\S+)", text, re.M)
        if m:
            api_key = m.group(1).strip()
        m = re.search(r"^model:\s*\n\s*base_url:\s*(\S+)", text, re.M)
        if m:
            base_url = m.group(1).strip().rstrip("/")
    return base_url, api_key


NINEROUTER_URL, NINEROUTER_KEY = load_ninerouter_creds()
MODEL = os.environ.get("NINEROUTER_MODEL", "free-burst")
CATEGORIES = {"user_pref", "project", "tool", "general"}


def tag_tokens(tags: str) -> set[str]:
    return {token.strip().lower() for token in (tags or "").split(",") if token.strip()}


def llm_classify(facts: list[dict], model: str) -> dict:
    """Call 9Router chat completions; returns {fact_id: verdict}.

    Retries transient failures: free-burst round-robins across providers
    and a slow/erroring route can stall or null-content a single call.
    Retry (2x, backoff) before giving up — a 10-fact batch on a slow route
    can exceed the 180s gateway timeout even when the same batch succeeds
    instantly on a different route (observed 2026-08-08: batch 5 timed out
    in cron, succeeded in 6.8s on retry with poolside/laguna-xs-2.1).
    """
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            return _classify_once(facts, model)
        except Exception as exc:
            last_err = exc
            if attempt < 2:
                time.sleep(5 * (attempt + 1))  # 5s, 10s backoff
    raise last_err  # type: ignore[misc]


def _classify_once(facts: list[dict], model: str) -> dict:
    payload = {
        "model": model,
        "stream": False,
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You classify holographic-memory auto-captured facts for a developer's "
                    "personal fact store. Given a JSON array of facts, return a JSON object "
                    "mapping each fact_id to a verdict. Verdict types:\n"
                    '  {"action":"keep","category":"user_pref|project|tool|general","tags":"comma,separated"} '
                    "- durable fact: rebucket to a non-auto_capture category, keep/rewrite tags.\n"
                    '  {"action":"remove"} - junk: ephemeral session material, PR states, commit '
                    "hashes, test counts, branch lists, price snapshots, raw user chat, "
                    "self-referential pointers, dups.\n"
                    '  {"action":"defer"} - uncertain: leave as-is, no llm-reviewed tag.\n'
                    "Rules: verify content before removing (a fact can contain trigger words like "
                    "'test'/'probe' while describing its own removal criteria). Keep configs, "
                    "workflows, project state, decisions, quirks, paths, rules. One fact = one "
                    "verdict. Respond with ONLY the JSON object, no markdown, no commentary."
                ),
            },
            {
                "role": "user",
                "content": "Facts:\n" + json.dumps(facts, ensure_ascii=False),
            },
        ],
    }
    req = urllib.request.Request(
        f"{NINEROUTER_URL}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {NINEROUTER_KEY}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        body = json.loads(resp.read().decode())
    content = body["choices"][0]["message"].get("content")
    if content is None:
        # 9Router transiently returns null content (model swap / error shape).
        # Do not crash the whole cron: report and let caller defer the batch.
        raise ValueError("LLM returned null content (transient 9Router response)")
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    start, end = content.find("{"), content.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"LLM returned non-JSON: {content[:500]}")
    return json.loads(content[start : end + 1])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--max", type=int, default=50,
                        help="Max facts to classify this run (0 = drain ALL pending). "
                        "Default 50 = bounded per cron run; use --max 0 for full drain.")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full JSON report (default: human summary for cron delivery).",
    )
    args = parser.parse_args()

    provider = load_memory_provider("hrr_memory")
    provider.initialize(session_id="cron-memory-housekeeping-minibatch")
    store = provider._store
    conn = store._conn
    result: dict[str, object] = {"mode": "dry-run" if args.dry_run else "live"}

    # --- 1. Deterministic junk (tag-based) ---
    junk_ids = [
        row["fact_id"]
        for row in conn.execute(
            "SELECT fact_id, tags, trust_score FROM facts WHERE trust_score <= 0.5"
        ).fetchall()
        if tag_tokens(row["tags"]) & {"test", "dummy", "probe"}
    ]
    if not args.dry_run:
        for fact_id in junk_ids:
            store.remove_fact(fact_id)
    result["deterministic_junk_removed"] = 0 if args.dry_run else len(junk_ids)

    # --- 2. Drain pending in mini-batches until 0 or --max cap ---
    total_kept = total_removed = total_deferred = 0
    rounds = 0
    while True:
        rows = conn.execute(
            """SELECT fact_id, category, tags, trust_score, created_at,
                      substr(content, 1, 500) AS content
               FROM facts ORDER BY fact_id"""
        ).fetchall()
        pending = [
            dict(row)
            for row in rows
            if (
                row["category"] == "auto_capture"
                or tag_tokens(row["tags"]) & {"auto_capture", "entity:cron"}
            )
            and "llm-reviewed" not in tag_tokens(row["tags"])
        ]
        if not pending:
            break
        batch = pending[: args.batch_size]
        if args.max:
            room = args.max - (total_kept + total_removed + total_deferred)
            if room <= 0:
                break
            batch = batch[:room]
            if not batch:
                break
        result["auto_capture_total_pending"] = len(pending)

        # --- 3. LLM classification (direct API, no agent) ---
        if args.dry_run:
            kept, removed, deferred = len(batch), 0, 0
        else:
            try:
                verdicts = llm_classify(batch, args.model)
            except Exception as exc:
                # Transient upstream failure (null content, 5xx, timeout):
                # defer the whole batch, stop quietly, exit 0 so cron stays silent.
                # Facts stay pending for the next run.
                result["classify_error"] = f"{type(exc).__name__}: {exc}"
                deferred_batch = len(batch)
                result["deferred"] = (result.get("deferred") or 0) + deferred_batch
                break
            kept = removed = deferred = 0
            for f in batch:
                v = verdicts.get(str(f["fact_id"])) or verdicts.get(f["fact_id"])
                if not v:
                    deferred += 1
                    continue
                action = v.get("action")
                if action == "remove":
                    store.remove_fact(f["fact_id"])
                    removed += 1
                elif action == "keep":
                    cat = v.get("category")
                    if cat not in CATEGORIES:
                        cat = "general"
                    tags = (v.get("tags") or "").strip(",") or "general"
                    store.update_fact(
                        f["fact_id"],
                        category=cat,
                        tags=f"{tags},llm-reviewed",
                        trust_delta=0.15,
                    )
                    kept += 1
                else:  # defer
                    deferred += 1
        total_kept += kept
        total_removed += removed
        total_deferred += deferred
        rounds += 1
        if args.dry_run:
            break  # dry-run doesn't mutate → pending never shrinks; one batch only
        if args.max and total_kept + total_removed + total_deferred >= args.max:
            break

    result["auto_capture_total_pending"] = (
        conn.execute(
            """SELECT COUNT(*) FROM facts
               WHERE (category='auto_capture' OR tags LIKE '%auto_capture%')
                 AND tags NOT LIKE '%llm-reviewed%'"""
        ).fetchone()[0]
    )
    result["batch_size"] = args.batch_size
    result["rounds"] = rounds
    result["kept"] = total_kept
    result["removed"] = total_removed
    result["deferred"] = total_deferred
    result["candidates"] = []  # no raw dump in summary mode

    # --- 4. Integrity maintenance ---
    no_hrr = conn.execute("SELECT COUNT(*) FROM facts WHERE hrr_vector IS NULL").fetchone()[0]
    rebuilt = 0
    if no_hrr and not args.dry_run:
        rebuilt = store.rebuild_all_vectors()
    result["missing_hrr_before"] = no_hrr
    result["hrr_rebuilt_facts"] = rebuilt

    result["facts_remaining"] = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    _emit(result, args.json)
    return 0


def _emit(result: dict, as_json: bool) -> None:
    """Print full JSON (--json) or a compact human summary (cron default)."""
    if as_json:
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return
    reviewed = result.get("kept", 0) + result.get("removed", 0) + result.get("deferred", 0)
    # Nothing to do → stay silent so cron delivers nothing
    if reviewed == 0 and not result.get("deterministic_junk_removed"):
        return
    lines = [
        f"🧠 Memory housekeeping: reviewed {reviewed} facts "
        f"({result.get('rounds', 0)} batch{'es' if result.get('rounds', 0) != 1 else ''} of {result.get('batch_size', 0)})",
        f"  kept: {result.get('kept', 0)} | removed: {result.get('removed', 0)} | deferred: {result.get('deferred', 0)}",
        f"  pending auto_capture: {result.get('auto_capture_total_pending', 0)} | total facts: {result.get('facts_remaining', 0)}",
    ]
    if result.get("missing_hrr_before"):
        lines.append(f"  hrr rebuilt: {result.get('hrr_rebuilt_facts', 0)}")
    if result.get("deterministic_junk_removed"):
        lines.append(f"  deterministic junk removed: {result.get('deterministic_junk_removed')}")
    if result.get("classify_error"):
        lines.append(f"  ⚠ classify skipped (transient): {result['classify_error']}")
    print("\n".join(lines))


if __name__ == "__main__":
    raise SystemExit(main())
