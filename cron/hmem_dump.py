#!/usr/bin/env python
"""Dump memory_store.db facts for review (read-only)."""
import sys

sys.path.insert(0, "/home/sonpham/.hermes/hermes-agent")

from plugins.memory import load_memory_provider

p = load_memory_provider("hrr_memory")
p.initialize(session_id="cron-review-dump")
store = p._store

rows = store._conn.execute(
    """SELECT fact_id, category, tags, trust_score, retrieval_count, helpful_count,
              (hrr_vector IS NOT NULL) AS has_hrr, (sbert_vector IS NOT NULL) AS has_sbert,
              created_at, substr(content, 1, 140) AS content
       FROM facts ORDER BY fact_id"""
).fetchall()

print(f"TOTAL={len(rows)}")
print("---")
for r in rows:
    print(
        f"{r['fact_id']}|{r['category']}|{r['tags']}|trust={r['trust_score']:.2f}|retr={r['retrieval_count']}|help={r['helpful_count']}|hrr={r['has_hrr']}|sbert={r['has_sbert']}|{r['created_at']}|{r['content']}"
    )
