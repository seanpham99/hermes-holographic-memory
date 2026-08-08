---
name: managing-hrr-memory
description: "Use for hrr_memory — probe, store, reason, clean."
metadata:
  hermes:
    tags: [memory, holographic, fact-store, recall, trust-scoring, cleanup]
    related_skills: [web-extraction]
---

# Managing Holographic Memory

Hermes Holographic Memory uses HRR (Holographic Reduced Representations) with local SQLite storage, trust scoring, and sub-millisecond algebraic retrieval. Use `fact_store` for structured lookup-on-demand; use `memory` for always-on system-prompt context.

## When to use which

| Store | Tool | For |
|-------|------|-----|
| **fact_store** | `fact_store(action=...)` | Structured facts: tool configs, priority chains, deploy procedures, error workarounds, project quirks. Lookup-on-demand, trust-scored. |
| **Regular memory** | `memory(action=...)` | Always-on context: system URLs, auth methods, hygiene rules, skill priority chains. Injected into every turn. |

**Rule**: if a fact is needed every conversation → regular memory. If it's situational or task-specific → fact_store. NEVER store the same fact in both. When in doubt → fact_store (probe first to avoid dupes).

## Intake protocol — MANDATORY on every write (prevents drift)

Ask the routing question on EVERY memory write:

> "Will I need this in EVERY future session, regardless of topic?"

- **YES** → `memory` tool only → memory.md (injected every turn, precious; keep entries <100 chars, one entry per fact).
- **NO / Maybe** → `fact_store` tool only → holographic store (on-demand probe, trust-scored).

**The write gate (BEFORE any `memory add`):**
1. `fact_store(action='search', query='<same fact keywords>')` — if it exists there, do NOT duplicate into memory.md. Reference it; the probe will surface it later.
2. Only if genuinely always-on (needed every session regardless of topic) → write to memory.md via the `memory` tool. NEVER hand-edit memory.md with `write_file`/`patch`/shell — it has a drift guard that will refuse or back up your rewrite. Use `memory(action='add'|'replace'|'remove')` only.

**Triplication anti-pattern:** the same fact in memory.md + fact_store + user profile = three sources of truth that drift. One fact = one store. If you catch a triplication, consolidate to the correct single store and remove from the others.

**Session-start probe (mandatory):** before advising on any project/entity, run:
```python
fact_store(action='probe', entity='<entity>')
fact_store(action='search', query='<keywords>')
```
Never pattern-match from memory.md alone — memory.md is always-on context, fact_store is the deep recall.

## Classify this session's learnings at every checkpoint

After each complex task (5+ tool calls), run the triage:
- Always-on (needed every session): `memory add`
- Situational (configs, project state, workflows, quirks): `fact_store add`
- Junk (test probes, session artifacts, one-off chat): drop

## Invocation — MANDATORY

**This skill fires on MULTIPLE triggers. If ANY match, you MUST invoke it:**

1. **Any task with 5+ tool calls** — run a memory checkpoint (probe → act → add → rate)
2. **Encountering an error or quirk** — probe if prior knowledge exists, then add the fix
3. **Completing a complex workflow** (install, config, organization, debugging) — add discovered patterns
4. **User mentions memory, recall, "remember", "learn", or "document this"** — full memory workflow
5. **Starting work on a tool/project with prior session history** — probe that entity first

**Anti-trigger:** "I'll do it next turn" or "This is too simple for memory" — these are rationalizations from the Red Flags table. Ignore them.

## Usage pattern (every non-trivial task)

```python
# 1. PROBE — before acting, check what we know
fact_store(action='probe', entity='project-name')
fact_store(action='search', query='relevant keywords')

# 2. ACT — do the work

# 3. ADD — after discovering patterns, store immediately
fact_store(action='add', content='discovered pattern', category='tool', tags='project,topic')

# 4. RATE — after confirming old facts were accurate
fact_feedback(action='helpful', fact_id=25)  # npx symlink issue was correct
```

## After 5+ tool calls (mandatory checkpoint)

Stop and ask: "Did I learn anything reusable in this batch?" If yes: `fact_store(action='add')`. Even a single fact per batch compounds into expert context over sessions. Zero facts stored after a complex task is a RED FLAG — it means you're either not learning or not documenting.

## Core actions

### Before making decisions: probe

Always probe entities relevant to the current task BEFORE acting. If the user asks about a project, tool, or domain with history, run:

```python
fact_store(action='probe', entity='<name>')
fact_store(action='search', query='<keywords>')
```

### Storing facts: add

When you discover a reproducible pattern, quirk, or workflow:

```python
fact_store(action='add', content='<fact>', category='...', tags='...')
```

Categories: `user_pref`, `project`, `tool`, `general`. Always tag with project name and topic for later retrieval. Keep facts atomic — one fact per add.

### Finding connections: reason + related

For compositional queries across entities:

```python
fact_store(action='reason', entities=['entity1', 'entity2'])
fact_store(action='related', entity='<name>')
```

Use `reason` when a decision touches multiple domains. Use `related` to discover linked facts.

### Detecting stale facts: contradict

Periodically check for conflicting claims:

```python
fact_store(action='contradict')
```

Facts that conflict indicate either an environment change or stale data. Resolve by updating or removing.

## Trust scoring

Every fact starts at trust_score 0.5. Use `fact_feedback` to train:

- **Helpful** (accurate, reusable): `fact_feedback(action='helpful', fact_id=N)` — trust rises
- **Unhelpful** (outdated, wrong): `fact_feedback(action='unhelpful', fact_id=N)` — trust decays

Rate facts AFTER using them — not preemptively. The store self-corrects over sessions.

## Recovery & inspection (2026-08-08)

**hrr_dim invariant:** the store is pinned to `hrr_dim=4096` everywhere (store.py default, retriever default, provider config schema default). Mixed-dim blobs (e.g. 4100B/1024-dim alongside 16388B/4096-dim) crash `fact_store search` with "HRR vector blob has N bytes; expected 16388". Recovery:

```bash
cd ~/.hermes/hermes-agent
venv/bin/python hrr_memory/scripts/rebuild_vectors.py   # from ~/Works/hermes-holographic-memory (standalone); backups to ~/.hermes/backups/, rebuilds all vectors+banks at 4096
```

Verify: `SELECT DISTINCT length(hrr_vector) FROM facts` → all `16388`; `SELECT bank_name, dim FROM memory_banks` → all `dim=4096`.

**White-box inspection (no LLM):**

```bash
venv/bin/python -m hrr_memory.export --out <dir>   # from ~/Works/hermes-holographic-memory (standalone); writes facts.md, entities.md, scenarios.md
```

**Cron interplay:** `memory-housekeeping-preflight.py` calls `rebuild_all_vectors()` with no dim — safe ONLY because the store default is now 4096. Never revert the default to 1024 without auditing that script.

## Cleanup cadence

After every complex task (5+ tool calls), check for junk:

```python
fact_store(action='search', query='dummy test probe read')
fact_store(action='contradict')
```

Remove immediately: test probes, factual errors, merged duplicates. Stale project facts decay naturally via trust scoring — only remove if explicitly wrong.

## Common anti-patterns

| Don't | Because | Instead |
|-------|---------|---------|
| Dump everything into regular memory | 2,200 char limit, crowded context | Use fact_store for lookup-on-demand |
| Store facts without tags | Unsearchable noise | Always tag with project + topic |
| Skip probe before decision | Acts on stale assumptions | Probe entities first |
| Leave probe/test facts | These are junk, not memory | Remove immediately after test |
| Store the same fact in both stores | Creates drift when one updates | Pick one store per fact type |
