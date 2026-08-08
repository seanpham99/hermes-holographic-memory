#!/usr/bin/env python3
"""Deterministic preflight for the hybrid memory-housekeeping cron.

Cleans only unambiguous junk and integrity defects. Prints bounded JSON for the
LLM to classify remaining auto_capture facts.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

AGENT_HOME = os.environ.get("HERMES_AGENT", "/home/sonpham/.hermes/hermes-agent")
if AGENT_HOME not in sys.path:
    sys.path.insert(0, AGENT_HOME)

from plugins.memory import load_memory_provider  # noqa: E402


def tag_tokens(tags: str) -> set[str]:
    return {token.strip().lower() for token in (tags or "").split(",") if token.strip()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Max auto_capture candidates emitted per run (mini-batch). "
        "Keep small so the agent's classification response stays under the "
        "output-length limit even after a large capture burst.",
    )
    args = parser.parse_args()

    provider = load_memory_provider("hrr_memory")
    provider.initialize(session_id="cron-memory-housekeeping-preflight")
    try:
        store = provider._store
        conn = store._conn
        result: dict[str, object] = {"mode": "dry-run" if args.dry_run else "live"}

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
        result["deterministic_junk_candidates"] = len(junk_ids)

        no_hrr = conn.execute(
            "SELECT COUNT(*) FROM facts WHERE hrr_vector IS NULL"
        ).fetchone()[0]
        rebuilt = 0
        if no_hrr and not args.dry_run:
            rebuilt = store.rebuild_all_vectors()
        result["missing_hrr_before"] = no_hrr
        result["hrr_rebuilt_facts"] = rebuilt

        no_sbert = conn.execute(
            "SELECT COUNT(*) FROM facts WHERE sbert_vector IS NULL"
        ).fetchone()[0]
        sbert_backfilled = 0
        # SBERT is a legacy/optional pipeline: the column may exist in
        # migrated stores while the plugin has no SBERT code at all.
        if hasattr(provider, "backfill_sbert_vectors") and no_sbert and not args.dry_run:
            sbert_backfilled = provider.backfill_sbert_vectors()
        result["sbert_supported"] = hasattr(provider, "backfill_sbert_vectors")
        result["missing_sbert_before"] = no_sbert
        result["sbert_backfilled_facts"] = sbert_backfilled
        result["missing_sbert_action"] = "skip-unsupported" if not hasattr(provider, "backfill_sbert_vectors") else ("backfilled" if sbert_backfilled else "none-missing")

        orphan_facts = conn.execute(
            "SELECT COUNT(*) FROM fact_entities WHERE fact_id NOT IN (SELECT fact_id FROM facts)"
        ).fetchone()[0]
        orphan_entities = conn.execute(
            "SELECT COUNT(*) FROM entities WHERE entity_id NOT IN (SELECT entity_id FROM fact_entities)"
        ).fetchone()[0]
        if not args.dry_run:
            conn.execute("DELETE FROM fact_entities WHERE fact_id NOT IN (SELECT fact_id FROM facts)")
            conn.execute("DELETE FROM entities WHERE entity_id NOT IN (SELECT entity_id FROM fact_entities)")
            conn.execute("VACUUM")
        result["orphan_fact_entities_removed"] = 0 if args.dry_run else orphan_facts
        result["orphan_entities_removed"] = 0 if args.dry_run else orphan_entities

        rows = conn.execute(
            """SELECT fact_id, category, tags, trust_score, created_at,
                      substr(content, 1, 500) AS content
               FROM facts ORDER BY fact_id"""
        ).fetchall()
        pending = [
            row for row in rows
            if (
                row["category"] == "auto_capture"
                or tag_tokens(row["tags"]) & {"auto_capture", "entity:cron"}
            )
            and "llm-reviewed" not in tag_tokens(row["tags"])
        ]
        # Mini-batch: emit only the OLDEST `--batch-size` pending facts so the
        # LLM classifies a bounded set and the response stays short. The rest
        # drain on subsequent runs once reviewed facts carry `llm-reviewed`.
        result["auto_capture_total_pending"] = len(pending)
        result["auto_capture_batch_size"] = args.batch_size
        result["auto_capture_candidates"] = [dict(row) for row in pending[: args.batch_size]]
        result["facts_remaining"] = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0
    finally:
        provider.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
