# SDD Plan-Brief Defects (caught by implementers, 2026-08-08)

When executing a plan via subagent-driven development, implementers WILL catch defects in the plan text. These are spec corrections, not task failures. Patterns observed while fixing the holographic store:

## 1. SQL idiom errors
Plan brief wrote `SELECT f.*, facts_fts.bm25(facts_fts)` — SQL syntax error in SQLite (`near "("`).
Correct: unqualified `bm25(facts_fts)`.
Lesson: verify SQL function call syntax against the actual engine before baking it into a brief.

## 2. Unsatisfiable test fixtures
Test asserted `res[1]` but the query matched only 1 fact → fails identically before AND after the change (proves nothing).
Implementer adjusted the dataset minimally (exact-match vs repeated-terms), preserved assertion intent, noted deviation in report.
Lesson: a TDD RED that fails for the same reason pre/post change is a broken test, not a failing feature.

## 3. Off-by-one sys.path
`Path(__file__).resolve().parents[3]` for a file 4 levels deep resolves to `plugins/`, not repo root.
Symptom: `ModuleNotFoundError: No module named 'hermes_state_common'` — identical to a missing-package error.
Fix: `parents[4]` = repo root; sys.path insert must precede the store import.

## 4. Behavior-neutral refactors
FTS5 default `rank` IS bm25 with default weights — swapping `rank` → explicit `bm25()` is behavior-neutral on the corpus today.
Still correct: enables future `bm25(facts_fts, w1, w2)` per-column weighting.
Lesson: park as deferred minor in the ledger; don't trigger a fix loop.

## Handling
- Accept the correction after verifying it (read the diff, confirm the fix is right).
- Record as `Task N: complete ... (review clean)` + a `minor (deferred)` or parked line so the final review sees both sides.
- Carry the corrected variant into later task briefs that reference the same API (e.g. keep `bm25(facts_fts)` in any later export/recall code).
- The implementer's report file is the persistent record — never discard it.
