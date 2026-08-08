# install.sh — install the hrr-memory plugin into $HERMES_HOME/plugins
# Usage: ./install.sh [HERMES_HOME]
set -euo pipefail

HERMES_HOME="${1:-$HOME/.hermes}"
PLUGIN_DIR="$HERMES_HOME/plugins"
mkdir -p "$PLUGIN_DIR"

# Symlink so updates to the repo propagate (no copy drift)
if [ -e "$PLUGIN_DIR/hrr_memory" ] && [ ! -L "$PLUGIN_DIR/hrr_memory" ]; then
  echo "ERROR: $PLUGIN_DIR/hrr_memory exists and is not a symlink. Remove it first." >&2
  exit 1
fi

ln -sfn "$(cd "$(dirname "$0")" ln -sfn "$(cd "$(dirname "$0")" && pwd)/hrr-memory"ln -sfn "$(cd "$(dirname "$0")" && pwd)/hrr-memory" pwd)/hrr_memory" "$PLUGIN_DIR/hrr_memory"
echo "Installed hrr_memory -> $PLUGIN_DIR/hrr_memory"
echo "Ensure ~/.hermes/config.yaml has:"
echo "  memory:"
echo "    provider: hrr-memory"
