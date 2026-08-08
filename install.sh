#!/usr/bin/env bash
# install.sh — install the hrr_memory plugin + cron scripts into $HERMES_HOME
# Usage: ./install.sh [HERMES_HOME]
set -euo pipefail

HERMES_HOME="${1:-$HOME/.hermes}"
PLUGIN_DIR="$HERMES_HOME/plugins"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- Plugin symlink (updates propagate, no copy drift) ---
mkdir -p "$PLUGIN_DIR"
if [ -e "$PLUGIN_DIR/hrr_memory" ] && [ ! -L "$PLUGIN_DIR/hrr_memory" ]; then
  echo "ERROR: $PLUGIN_DIR/hrr_memory exists and is not a symlink. Remove it first." >&2
  exit 1
fi
ln -sfn "$REPO_DIR/hrr_memory" "$PLUGIN_DIR/hrr_memory"
echo "Installed hrr_memory -> $PLUGIN_DIR/hrr_memory"

# --- Cron scripts (Hermes cron references ~/.hermes/scripts/<name>) ---
# COPIES, not symlinks: the Hermes cron runner resolves the script path and
# rejects any file whose realpath escapes ~/.hermes/scripts/ (symlink escape
# guard in cron/scheduler.py). A symlinked script fails at fire time with
# "Blocked: script path resolves outside the scripts directory". Re-running
# install.sh refreshes the copies, so the repo stays the source of truth.
SCRIPTS_DIR="$HERMES_HOME/scripts"
mkdir -p "$SCRIPTS_DIR"
for f in cron/*.py; do
  base="$(basename "$f")"
  cp "$REPO_DIR/$f" "$SCRIPTS_DIR/$base"
  chmod +x "$SCRIPTS_DIR/$base"
done
echo "Copied cron scripts into $SCRIPTS_DIR"

echo
echo "Ensure ~/.hermes/config.yaml has:"
echo "  memory:"
echo "    provider: hrr_memory"
