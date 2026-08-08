# Memory Housekeeping Cron Scripts

Operational scripts for the `hrr_memory` provider — versioned here so the cron's brain lives with the plugin.

## Scripts

| Script | Purpose |
|--------|---------|
| `memory-housekeeping-minibatch.py` | **The cron job** (`b7ba63551355`, every 12h, no_agent). Deterministic junk (tag-based) + LLM-classify up to 40 pending `auto_capture` facts. `--dry-run` for preview, `--max 0` full drain, `--json` machine output. |
| `memory-housekeeping-preflight.py` | Deterministic preflight: junk/orphan/VACUUM + conditional HRR rebuild + SBERT report. Safe to run anytime. |
| `hmem_review.py` / `hmem_review_run.py` | Full-store review + run (junk/duplicate/stale sweep). |
| `hmem_dump.py` | Full fact dump. |
| `hmem_backfill_llm_reviewed.py` | Re-process auto-captured facts tagged `llm-reviewed`. |
| `housekeeping-review.py` | Housekeeping sweep entrypoint. |

All call `load_memory_provider("hrr_memory")` — they resolve the **active** provider from the standalone plugin (`~/.hermes/plugins/hrr_memory` → this repo). Same `memory_store.db` as the runtime.

## Install

```bash
# install.sh copies cron/*.py into ~/.hermes/scripts/ (see repo root)
./install.sh
# or manually:
cp cron/*.py ~/.hermes/scripts/
chmod +x ~/.hermes/scripts/*.py
```

**COPIES, not symlinks.** The Hermes cron runner (`cron/scheduler.py`) resolves the script path and blocks any file whose realpath escapes `~/.hermes/scripts/` — a symlink to this repo fails at fire time with "Blocked: script path resolves outside the scripts directory". Re-running `install.sh` refreshes the copies, so this repo stays the source of truth.

The Hermes cron job `memory-housekeeping` references `~/.hermes/scripts/memory-housekeeping-minibatch.py` by name.

## Notes

- **Free-burst rule**: no LLM calls in the deterministic scripts; the minibatch's `llm_classify` uses the configured gateway (free-burst model) with 3x retry/backoff.
- **hrr_dim invariant**: preflight calls `rebuild_all_vectors()` with NO dim — safe only because the store default is pinned to 4096. Never revert the default.
- Scripts must run from the hermes-agent repo (`venv/bin/python`) so `plugins.memory` + `hermes_state` import.
