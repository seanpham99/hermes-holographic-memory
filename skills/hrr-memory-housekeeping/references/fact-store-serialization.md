# fact_store serialization failure — debugging recipe (2026-08-04)

## Symptom

`fact_store(action='search', ...)` → `{"error": "Object of type bytes is not JSON serializable"}`
while `action='probe'` may still work. Happens only with prod config (hrr_weight > 0); a config with
`hrr_weight=0.0` skips the HRR branch and can mask the bug.

## Root cause

`FactRetriever` strips `hrr_vector` (BLOB) from result dicts before returning, but NOT `sbert_vector`
(a 1536-byte BLOB column added by the SBERT backfill era). Both are pulled by the `SELECT f.*` in
`_fts_candidates()` and the per-vector SELECTs. `json.dumps({"results": results})` in
`plugins/memory/holographic/__init__.py::_handle_fact_store` then throws.

Six leak sites in `plugins/memory/holographic/retrieval.py`:
1. `search()` strip loop (line ~119) — only popped `hrr_vector`
2-5. The four `fact_vec = hrr.bytes_to_phases(fact.pop("hrr_vector"), ...)` sites (probe category path, related, reason, nearest)
6. `contradict()` clean-dict filter — `{k: v for k, v in f.items() if k != "hrr_vector"}`

## Debugging path (how it was found)

1. Reproduce with the REAL store path — `~/.hermes/memory_store.db` (NOT `~/.hermes/holographic-memory/facts.db`, which is a different/empty store). The tool config uses `db_path: ~/.hermes/memory_store.db`.
2. Run via `execute_code` (import plugin directly, `sys.path.insert(0, "/home/sonpham/.hermes/hermes-agent")`) — the terminal tool's lifecycle guard misparses commands containing "hermes" paths and can throw spurious `embedded null byte` errors.
3. Inspect `r._fts_candidates("PTG", None, 0.3, 30)[0]` keys → both `hrr_vector` and `sbert_vector` present as bytes.
4. Simulate fix: `f.pop("sbert_vector", None)` → `json.dumps` passes → root cause confirmed.

## Fix (committed son/dev e8c582eae)

```python
# search strip loop
for fact in results:
    fact.pop("hrr_vector", None)
    fact.pop("sbert_vector", None)

# each bytes_to_phases site — add right after
fact.pop("sbert_vector", None)

# contradict filter
if k not in ("hrr_vector", "sbert_vector")
```

## Verification

```python
from plugins.memory.holographic.retrieval import FactRetriever
from plugins.memory.holographic.store import MemoryStore
import json, os
store = MemoryStore(db_path=os.path.expanduser("~/.hermes/memory_store.db"))
r = FactRetriever(store)
for action in [("search", lambda: r.search("PTG", limit=5)),
               ("probe", lambda: r.probe("PTG", limit=5)),
               ("related", lambda: r.related("PTG", limit=5)),
               ("reason", lambda: r.reason(["PTG", "Brad"], limit=5)),
               ("contradict", lambda: r.contradict(limit=5))]:
    json.dumps({"results": action[1]()})  # must not raise
```

## Gotcha

The gateway process caches Python modules — after patching `retrieval.py`, the live `fact_store` tool
keeps failing until `hermes gateway restart` (run from a shell OUTSIDE the gateway; the lifecycle
guard blocks in-gateway restarts by design because it would kill the session).
