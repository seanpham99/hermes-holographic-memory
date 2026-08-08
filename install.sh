# install.sh — install the holographic memory plugin into $HERMES_HOME/plugins
# Usage: ./install.sh [HERMES_HOME]
set -euo pipefail

HERMES_HOME="${1:-$HOME/.hermes}"
PLUGIN_DIR="$HERMES_HOME/plugins"
mkdir -p "$PLUGIN_DIR"

# Symlink so updates to the repo propagate (no copy drift)
if [ -e "$PLUGIN_DIR/holographic" ] && [ ! -L "$PLUGIN_DIR/holographic" ]; then
  echo "ERROR: $PLUGIN_DIR/holographic exists and is not a symlink. Remove it first." >&2
  exit 1
fi

ln -sfn "$(cd "$(dirname "$0")" && pwd)/holographic" "$PLUGIN_DIR/holographic"
echo "Installed holographic -> $PLUGIN_DIR/holographic"
echo "Ensure ~/.hermes/config.yaml has:"
echo "  memory:"
echo "    provider: holographic"
