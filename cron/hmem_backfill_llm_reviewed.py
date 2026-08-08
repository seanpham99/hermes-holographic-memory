#!/usr/bin/env python3
"""Backfill llm-reviewed tags on older auto_capture facts already classified
by earlier housekeeping runs (facts with category != auto_capture but still
carrying the auto_capture tag and no llm-reviewed tag)."""
from __future__ import annotations

import os
import sys

AGENT_HOME = os.environ.get("HERMES_AGENT", "/home/sonpham/.hermes/hermes-agent")
if AGENT_HOME not in sys.path:
    sys.path.insert(0, AGENT_HOME)

from plugins.memory import load_memory_provider  # noqa: E402


def main() -> int:
    provider = load_memory_provider("hrr_memory")
    provider.initialize(session_id="cron-memory-housekeeping-backfill")
    store = provider._store
    conn = store._conn
    rows = conn.execute(
        "SELECT fact_id, tags FROM facts WHERE category != 'auto_capture' AND tags LIKE '%auto_capture%'"
    ).fetchall()
    updated = 0
    for row in rows:
        tags = {t.strip().lower() for t in (row["tags"] or "").split(",") if t.strip()}
        if "llm-reviewed" not in tags:
            store.update_fact(row["fact_id"], tags=row["tags"] + ",llm-reviewed")
            updated += 1
    remaining = conn.execute(
        "SELECT COUNT(*) FROM facts WHERE (category='auto_capture' OR tags LIKE '%auto_capture%') AND tags NOT LIKE '%llm-reviewed%'"
    ).fetchone()[0]
    print(f"backfilled={updated} auto_capture_not_reviewed={remaining}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
