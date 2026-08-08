# Memory Routing Enforcement (L1 + L2)

How the triplication problem was permanently solved (2026-08-05) — the
mechanisms, the storage internals they rely on, and the incident that
motivated the sweep.

## The problem

Same fact was landing in THREE surfaces: memory.md + fact_store + user
profile. Root cause: no intake protocol — the agent probed and classified
per session but had no hard gate, so facts drifted into duplication.

## L1 — system-prompt gate (prevention)

`plugins/memory/holographic/__init__.py` → `system_prompt_block()`:

- BOTH branches (empty store + populated store) now return a
  `## MANDATORY memory routing gate` block. If only the populated branch is
  patched, a fresh-profile session skips the rule.
- Content: ask "Will I need this in EVERY future session?" YES → memory
  tool only; NO/Maybe → fact_store only; NEVER both; probe fact_store
  before a memory add; memory.md mutations only via the memory tool.
- Shipped on `feat/holographic-auto-capture` PR and cherry-picked to
  `son/dev` (commit 90be8c334).
- Verify after patching: `python3 -c "import inspect; from
  plugins.memory.holographic import HolographicMemoryProvider; src =
  inspect.getsource(HolographicMemoryProvider.system_prompt_block); assert
  src.count('MANDATORY memory routing gate') == 2"` — both branches carry it.

## L2 — housekeeping cron sweep (catch residue)

Cron `memory-housekeeping` (b7ba63551355, 2×/day 11:00/23:00) prompt
extended with a duplicate-routing sweep: read MEMORY.md + USER.md, probe
fact_store per entry, remove memory.md dups via the `memory` tool, report
or `[SILENT]`.

## Storage internals that make the sweep safe

- `ENTRY_DELIMITER = "\n§\n"` in `tools/memory_tool.py` and
  `hermes_cli/agent_import.py`. Splitting on bare "§" would split entries
  that contain "§" in content.
- `MemoryStore._detect_external_drift` backs up `<name>.bak.<ts>` and
  REFUSES `replace`/`remove` when: (a) the file doesn't round-trip through
  the parser, or (b) any single entry exceeds the whole-file char limit.
  Hand-edits (write_file/patch/shell append) become "one giant entry" →
  refused. So the sweep must mutate via the `memory` tool only.
- `add` is append-only and skips the drift guard, but still rewrites the
  whole file; a file that reads as EMPTY (transient lock/IO error) is
  refused — prevents wiping all prior memory on a bad read.

## The 2026-08-01 reset incident (why tests went missing)

`hermes-daily-update.sh` (cron 31def2a67be1) ran `git reset --hard
upstream/main` while current branch was `son/dev` (script never checked
out main first; unqualified merge/reset acted on the checked-out branch).
Wiped un-pushed commits from son/dev including the holographic auto-capture
TESTS (origin/son/dev froze at 46cf44267). Plugin code (`capture.py` etc.)
was re-added later; the tests were not.

Lesson: daily-sync scripts must refuse unless current branch is `main`, or
use an isolated worktree. Recovery for orphaned files: find them via
`git log --all --diff-filter=A -- <path>` / `git branch -a --contains
<sha>`, restore from the surviving ref (feature branch or
`refs/remotes/origin/backup/origin-son-dev-YYYYMMDD`).

## add_fact API change pitfall (auto-capture feature)

`store.py` `add_fact` changed from `-> int` to `-> dict {fact_id, status}`
(when `initial_trust` + semantic dedup were added). The caller
`_handle_fact_store` in `__init__.py` was NOT updated → `fact_store add`
returned the whole dict as `fact_id`, corrupting the tool response. This
was a latent bug on BOTH son/dev and the PR branch, masked because the
tests were missing. Pattern: when a store method's return type changes,
grep ALL callers (`grep -rn "add_fact" --include="*.py"`) — mocks in tests
need the new signature too (benchmark FakeStore lacked `initial_trust` →
TypeError swallowed → 0 facts stored).
