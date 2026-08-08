#!/usr/bin/env python
"""Holographic memory review: junk/dup/stale/entity:cron/HRR-missing + contradict scan + clean."""
import sys

sys.path.insert(0, "/home/sonpham/.hermes/hermes-agent")

from plugins.memory import load_memory_provider

p = load_memory_provider("hrr_memory")
p.initialize(session_id="cron-hmem-review")
store = p._store
retriever = p._retriever

conn = store._conn


def dump_all() -> list:
    return conn.execute(
        """SELECT fact_id, category, tags, trust_score, retrieval_count, helpful_count,
                  (hrr_vector IS NOT NULL) AS has_hrr, (sbert_vector IS NOT NULL) AS has_sbert,
                  substr(content, 1, 200) AS content
           FROM facts ORDER BY fact_id"""
    ).fetchall()


before = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]

# 1. junk/dup/stale candidates (tag or content markers)
for q in ("dummy", "test", "probe", "auto_capture", "session log"):
    rows = conn.execute(
        """SELECT fact_id, tags, trust_score, substr(content,1,160) c
           FROM facts WHERE tags LIKE ? OR tags LIKE ? OR tags LIKE ? OR tags LIKE ?
              OR content LIKE ?""",
        (f"{q},%", f"%,{q}", f"%,{q},%", q, f"%{q}%"),
    ).fetchall()
    print(f"== tag/content '{q}': {len(rows)} hits")
    for r in rows:
        print(f"  {r['fact_id']}|tags={r['tags']}|trust={r['trust_score']:.2f}|{r['c']}")

# 2. entity:cron tag
print("== entity:cron")
for r in conn.execute(
    """SELECT fact_id, category, tags, trust_score, substr(content,1,160) c FROM facts
       WHERE tags LIKE '%cron%' ORDER BY fact_id"""
).fetchall():
    print(f"  {r['fact_id']}|cat={r['category']}|tags={r['tags']}|trust={r['trust_score']:.2f}|{r['c']}")

# 3. missing HRR vectors
print("== missing HRR")
for r in conn.execute(
    "SELECT fact_id, category, substr(content,1,120) c FROM facts WHERE hrr_vector IS NULL"
).fetchall():
    print(f"  {r['fact_id']}|{r['category']}|{r['c']}")

# 4. missing SBERT
print("== missing SBERT")
for r in conn.execute(
    "SELECT fact_id, category, substr(content,1,120) c FROM facts WHERE sbert_vector IS NULL"
).fetchall():
    print(f"  {r['fact_id']}|{r['category']}|{r['c']}")

# 5. contradict scan
print("== contradict")
try:
    for pair in retriever.contradict(limit=10):
        print(f"  {pair}")
except Exception as e:
    print(f"  ERROR: {e}")

print(f"TOTAL_BEFORE={before}")
