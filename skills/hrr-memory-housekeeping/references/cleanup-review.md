# Cleanup review — worked example (2026-07-31, 275 → 97 facts)

Canonical reference for a full holographic fact-store review run. Numbers are from the
2026-07-31 housekeeping run on this machine; re-verify against the live DB each run.

## Outcome

- 275 → 97 facts (removed 178, updated 35, rebucketed survivors)
- VACUUM: 2,727,936 → 1,179,648 bytes (~1.5 MB reclaimed)
- Contradictions resolved: 4 (see below)
- Orphaned fact_entities: 7 deleted; unlinked entities: 13 deleted
- FTS orphans: 0 (triggers keep `facts_fts` synced — expect 0)
- HRR missing: 0 (no rebuild needed); SBERT missing: 45 (embedder absent in cron env — deferred, not a bug)
- Final categories: project 39, tool 37, general 12, user_pref 11

## Junk taxonomy (what to remove)

1. **PR/commit/merge ephemera** — "PR #74900 open, head e52ecbb67", "3 changed files",
   "squashed, force-pushed", review-comment IDs, branch lists, head SHAs. State lives in
   git/GitHub; stale within hours. (~90 facts in this run.)
2. **Working-tree/git-sync snapshots** — "working tree clean", "son/dev is 11 commits behind",
   "main reset to upstream/main". Covered by fact 125-style canonical workflow facts.
3. **Market/financial price snapshots** — "HPG 28/7 +4.22%", "BTC ~$64,400", "VIC P/E ~98x",
   Q2 earnings %s. One-moment observations; stale-prone.
4. **Self-referential pointers** — "Fact id 405 stored", "Stored facts: 430-433", "fact #349
   references", "facts 233 & 225 updated". Not facts.
5. **Raw user chat captured verbatim** — e.g. "Good, skip the openbb. I want you to explore...".
   Same class as the previously-removed 150-152/190/72. Always remove.
6. **Session logs / housekeeping run logs** — "VACUUM reclaimed 12KB", "18 tests pass",
   "cron prompt now: ...". Duplicated in cron log dir + this skill's references.
7. **Dups of regular memory / skills** — install paths, repo remotes, gh auth account,
   "edgartools requires set_identity" (documented in finance-data skill), js-autofix case
   (documented in github-actions-debugging/references/js-autofix-fork-case.md).
8. **Exact dups within store** — keep the one with the best tags/category; remove the rest.

## Contradiction resolutions (worked examples)

| Facts | Conflict | Resolution |
|-------|----------|------------|
| 77 vs 430 | vnstock modular API (`vnstock.api.quote.Quote`) vs verified "needs `import vnstock.explorer.*`" | Remove 77 (trust 0.3), keep 430 |
| 46 vs 346/347 | PTG ticket statuses | Merge 346/347 into 46 in place |
| 75 vs 322 | PR inventory (3 PRs vs 5 PRs) | Merge into 75 (add 75251/75252) |
| 276 vs 330 | `hermes update` pulls upstream vs fork | Both ephemera; remove both, keep canonical 125 |

Pattern: **update the surviving fact in place** (search/probe keep returning it) rather than
deleting both; for same-topic ephemera where neither is canonical, delete both and rely on the
canonical fact.

## Verification checklist (after apply)

```sql
SELECT COUNT(*) FROM facts;
SELECT COUNT(*) FROM facts WHERE hrr_vector IS NULL;      -- expect 0
SELECT COUNT(*) FROM facts WHERE sbert_vector IS NULL;    -- may be >0 (see pitfall)
SELECT category, COUNT(*) FROM facts GROUP BY category;
-- FTS orphan check:
SELECT COUNT(*) FROM facts_fts f LEFT JOIN facts t ON t.fact_id = f.rowid WHERE t.fact_id IS NULL;
-- entity orphan check:
SELECT COUNT(*) FROM fact_entities fe LEFT JOIN facts f ON f.fact_id = fe.fact_id WHERE f.fact_id IS NULL;
SELECT COUNT(*) FROM entities e LEFT JOIN fact_entities fe ON fe.entity_id = e.entity_id WHERE fe.entity_id IS NULL;
```

Plus: `retriever.contradict(limit=10)` → expect 0 pairs; search round-trip on a known fact.

## Working scripts (idempotent, safe to re-run)

- `~/.hermes/scripts/hmem_dump.py` — full dump with trust/vector flags
- `~/.hermes/scripts/hmem_review.py` — tag/content scans + missing-vector + contradict scan
- `~/.hermes/scripts/hmem_review_run.py` — REMOVE/UPDATE lists + clean() + post-report
  (before re-running: verify `set(REMOVE) & set(UPDATE)` is empty)
