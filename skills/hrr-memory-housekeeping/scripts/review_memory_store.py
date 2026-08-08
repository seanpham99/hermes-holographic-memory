#!/usr/bin/env python
"""Holographic memory_store.db review scaffold (read-only scan).

Works without the fact_store tool (cron/headless): uses the MemoryStore API
directly. Dump + junk/tag scans + missing-vector check + contradict scan.

Usage: python3 review_memory_store.py [db_path]
Extend REMOVE/UPDATE lists in a copy of this script per run; the apply step
lives in the companion run script (see references/cleanup-review.md).
"""
import sys

HERMES_AGENT = "/home/sonpham/.hermes/hermes-agent"
if HERMES_AGENT not in sys.path:
    sys.path.insert(0, HERMES_AGENT)

from plugins.memory import load_memory_provider  # noqa: E402

p = load_memory_provider("hrr_memory")
p.initialize(session_id="cron-hmem-review")
store = p._store
retriever = p._retriever
conn = store._conn

# 1. Full dump (review EVERYTHING before touching anything)
rows = conn.execute(
    """SELECT fact_id, category, tags, trust_score, retrieval_count, helpful_count,
              (hrr_vector IS NOT NULL) AS has_hrr, (sbert_vector IS NOT NULL) AS has_sbert,
              created_at, substr(content, 1, 140) AS content
       FROM facts ORDER BY fact_id"""
).fetchall()
print(f"TOTAL={len(rows)}")
for r in rows:
    print(
        f"{r['fact_id']}|{r['category']}|{r['tags']}|trust={r['trust_score']:.2f}|"
        f"retr={r['retrieval_count']}|help={r['helpful_count']}|hrr={r['has_hrr']}|"
        f"sbert={r['has_sbert']}|{r['created_at']}|{r['content']}"
    )

# 2. Junk tag/content scans
for q in ("dummy", "test", "probe", "auto_capture", "session log"):
    hits = conn.execute(
        """SELECT fact_id, tags, trust_score, substr(content,1,160) c
           FROM facts WHERE tags LIKE ? OR tags LIKE ? OR tags LIKE ? OR tags LIKE ?
              OR content LIKE ?""",
        (f"{q},%", f"%,{q}", f"%,{q},%", q, f"%{q}%"),
    ).fetchall()
    print(f"== tag/content '{q}': {len(hits)} hits")
    for h in hits:
        print(f"  {h['fact_id']}|tags={h['tags']}|trust={h['trust_score']:.2f}|{h['c']}")

# 3. Missing vectors (rebuild_all_vectors only if hrr NULLs > 0)
print("== missing HRR")
for r in conn.execute(
    "SELECT fact_id, category, substr(content,1,120) c FROM facts WHERE hrr_vector IS NULL"
).fetchall():
    print(f"  {r['fact_id']}|{r['category']}|{r['c']}")

print("== missing SBERT")
for r in conn.execute(
    "SELECT fact_id, category, substr(content,1,120) c FROM facts WHERE sbert_vector IS NULL"
).fetchall():
    print(f"  {r['fact_id']}|{r['category']}|{r['c']}")

# 4. Contradiction scan
print("== contradict")
try:
    for pair in retriever.contradict(limit=10):
        print(f"  {pair}")
except Exception as exc:  # numpy absent -> returns [] per API, but guard anyway
    print(f"  ERROR: {exc}")

p.shutdown()
