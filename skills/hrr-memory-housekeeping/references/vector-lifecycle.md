# Vector lifecycle: HRR vs SBERT

## Two independent vectors

- **HRR**: the active `MemoryStore.add_fact()` path computes HRR after entity linking. `rebuild_all_vectors()` repairs missing HRR vectors.
- **SBERT**: optional semantic embedding used for semantic dedup/search in semantic-enabled builds. A `sbert_vector` column alone does not prove SBERT is active.

## Live-capability check

Before claiming capture-time embedding or backfill support, inspect the loaded provider/store:

```python
store = provider._store
hasattr(store, "_compute_sbert_vector")
hasattr(store, "backfill_sbert_vectors")
hasattr(store, "clean")
```

Also inspect `add_fact()` for the actual call path. Do not infer behavior from an old skill, schema column, historical commit, or stale cron prompt.

## Capture semantics

Auto-capture uses the same `add_fact()` persistence path as ordinary facts unless the active caller proves otherwise. Therefore:

- if `add_fact()` calls only `_compute_hrr_vector()`, new auto-captures get HRR only;
- LLM categorization changes semantic metadata, not embeddings;
- `update_fact()` only regenerates a vector when its implementation explicitly does so after content changes.

## Backfill semantics

A supported SBERT backfill selects `sbert_vector IS NULL`, embeds each fact's content, serializes the vector, and updates only that column. It should be an explicit bounded maintenance operation, not silently run on every housekeeping tick.

## Verification checklist

Report separately:

```sql
SELECT COUNT(*),
       SUM(hrr_vector IS NULL),
       SUM(sbert_vector IS NULL)
FROM facts;
```

Then verify the active store exposes the backfill method and that one new test fact follows the intended insertion path. NULL SBERT does not imply broken memory when FTS/HRR remain available.
