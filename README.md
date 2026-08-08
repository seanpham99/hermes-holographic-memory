# Hermes Holographic Memory Plugin

Standalone Hermes Agent memory provider: a local SQLite fact store with HRR (Holographic Reduced Representations) algebraic retrieval, FTS5/BM25 hybrid keyword recall, trust scoring, contradiction detection, white-box artifact export, and L2 scenario grouping.

**No LLM runtime cost.** Every operation is local math — no embeddings, no API calls, free-burst cron friendly.

## Features

- **HRR algebraic recall** — `probe`, `related`, `reason` (multi-entity vector JOIN), `contradict` (memory hygiene nobody else has)
- **Hybrid retrieval** — BM25 (FTS5) + Jaccard + HRR similarity, trust-weighted
- **Trust scoring** — facts start at 0.5, feedback trains them asymmetrically
- **White-box export** — `python -m hrr_memory.export` writes `facts.md`, `entities.md`, `scenarios.md` (human-readable, inspectable, no black box)
- **L2 scenario grouping** — heuristic clustering (token or capitalized-entity overlap), no LLM
- **Entity resolution** — auto-links facts to entities, alias-aware
- **Auto-capture (optional)** — tool observations captured into facts via context-aware LLM compression (off by default)
- **Migration utility** — `rebuild_vectors.py` recovers from mixed-dim corruption (backup first)

## Install

The plugin loader scans `$HERMES_HOME/plugins/` (default `~/.hermes/plugins/`) for memory providers. Install by symlink:

```bash
mkdir -p ~/.hermes/plugins
ln -sfn "$(pwd)/hrr-memory" ~/.hermes/plugins/hrr-memory
```

Or copy:

```bash
mkdir -p ~/.hermes/plugins
cp -r hrr-memory ~/.hermes/plugins/
```

Then configure in `~/.hermes/config.yaml`:

```yaml
memory:
  provider: hrr-memory
```

## Usage

### CLI export

```bash
cd /path/to/hermes-agent   # needs hermes-agent on sys.path
venv/bin/python -m hrr_memory.export --out /tmp/memory-export
# writes facts.md, entities.md, scenarios.md
```

### Migration / recovery

```bash
venv/bin/python hrr-memory/scripts/rebuild_vectors.py   # backup first, rebuild at dim=4096
```

### In-session (fact_store tool)

The Hermes `fact_store` / `fact_feedback` tools drive the provider:
- `fact_store(action='add', content=..., category=..., tags=...)`
- `fact_store(action='search', query=...)` — hybrid BM25+HRR
- `fact_store(action='probe', entity=...)` — algebraic entity recall
- `fact_store(action='reason', entities=[...])` — multi-entity intersection
- `fact_store(action='related', entity=...)` — structural neighbors
- `fact_store(action='contradict')` — find conflicting facts
- `fact_feedback(action='helpful'|'unhelpful', fact_id=...)` — train trust

## Configuration

| Key | Default | Description |
|-----|---------|-------------|
| `db_path` | `$HERMES_HOME/memory_store.db` | SQLite database path |
| `hrr_dim` | `4096` | HRR vector dimensions (DO NOT change after first write) |
| `default_trust` | `0.5` | Default trust score for new facts |
| `auto_capture` | `false` | Auto-capture tool observations via LLM |
| `capture_interval` | `5` | Auto-capture: compress every N turns |

## Architecture

```
plugins/memory/hrr-memory/
├── __init__.py       # MemoryProvider, config schema, CLI/TUI commands
├── store.py          # MemoryStore: SQLite + FTS5 + HRR vectors + trust
├── retrieval.py      # FactRetriever: BM25 + Jaccard + HRR hybrid scoring
├── hrr-memory.py    # HRR primitives (bind/unbind/bundle, phase encoding)
├── capture.py        # optional auto-capture via LLM compression
├── export.py         # white-box markdown artifacts + CLI
└── scripts/
    └── rebuild_vectors.py   # migration: rebuild all vectors at fixed dim
```

## Requirements

- Python 3.11+
- numpy
- Hermes Agent (for `hermes_constants`, `hermes_state`, `agent.memory_provider`, `plugins.memory` loader)

## License

MIT — see LICENSE.
