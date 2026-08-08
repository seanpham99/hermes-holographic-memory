# TencentDB-Agent-Memory — comparison & steal list

Evaluated 2026-08-08. Repo: `github.com/TencentCloud/TencentDB-Agent-Memory` (MIT, ~12k stars, Node >=22.16).

## What it is

Team-level memory hub producing 4 reusable assets: **Chat Memory, Skill, LLM-Wiki, CodeGraph**. Two architectural pillars:

1. **Symbolic short-term memory** — offloads verbose tool logs to external `refs/*.md`; keeps a compact **Mermaid canvas** of task-state transitions in context; `node_id` drill-down retrieves raw text on demand. Claims: −61.38% tokens, +51.52% pass rate on WideSearch (vs OpenClaw baseline).
2. **Layered long-term memory** — L0 Conversation → L1 Atom → L2 Scenario → L3 Persona semantic pyramid instead of flat vector pile. PersonaMem accuracy 48% → 76%.

Storage: SQLite + sqlite-vec (local) or Tencent Cloud Vector DB. Retrieval: hybrid BM25 + vector + RRF. Has Hermes Gateway adapter (`memory_tencentdb` provider) — but it is a Node sidecar on `:8420` with its own LLM gateway (`TDAI_LLM_*` keys) doing extraction/recall.

## v2 research (2026-08-08, MemoryCore deep-read)

- **Their Hermes integration REPLACES the provider, it doesn't extend it.** Install = symlink `hermes-plugin/memory/memory_tencentdb` into `~/.hermes/hermes-agent/plugins/memory/` + `memory.provider: memory_tencentdb` in config + Node Gateway on `:8420`. It swaps OUT holographic entirely.
- **Known limitations (INSTALL.md):** Hermes/OpenClaw need static `x-task-id` + `x-conversation-id` headers; missing → session bypass (no memory injection, no recording). `x-task-id` is required in current version — adds onboarding friction (must create Task in panel + hardcode). Incomplete for our use.
- **Full stack is 4 services:** MemoryCore (:8420), Panel (:8125), Knowledge (:8424), Proxy (:8096). MemoryCore is TypeScript — concepts are stealable, code is not extractable into our Python store.
- **Architecture:** L0 raw dialogue captured to SQLite; background workers extract L1 atom → L2 scene → L3 persona as thresholds hit. v3 data plane requires team/agent/user isolation IDs.

## Verdict for this setup (single-user, free-burst, holographic HRR)

**Do not switch.** Costs: Node >=22.16 sidecar + per-conversation LLM extraction calls — breaks the cron=free-burst rule. Loses what holographic already has: zero-cost HRR algebraic recall, trust scoring, `contradict()` hygiene, `reason`/`related` compositionality. Their team-hub payoff targets multi-agent/multi-user orgs; Son's cluster question is multi-device *sharing*, which their roadmap ("portable memory") doesn't even ship yet.

**Steal list (priority order):**
1. **Hybrid recall** — holographic already has FTS5 keyword + Jaccard + HRR; upgrade FTS5 rank to BM25 (`facts_fts.bm25(facts_fts)`). Native SQLite, free.
2. **White-box artifacts** — Tencent's best idea: readable markdown memory layers for inspection/debug (ours is a flat SQLite blob). Export `facts.md`/`entities.md`/`scenarios.md` via stdlib. See plan Task 4–6.
3. **L2 Scenario grouping** — cluster atomic facts into scene blocks by entity/token overlap heuristic (no LLM). Gives retrieval macro-guidance.
4. **node_id trace / context offload** — skip; headroom/CCR skills already cover token pressure.

## Provenance

Full plan: `~/.hermes/artifact/tencentdb-memory-steal/output/tencentdb-memory-steal-plan.md`.
