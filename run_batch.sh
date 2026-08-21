#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

for f in ~/Downloads/Vinland/*.pdf ~/Downloads/Vinland\ Saga/*.pdf; do
    [ -f "$f" ] || continue
    echo "Processing: $f"
    python3 "$SCRIPT_DIR/kcc-c2e.py" -d -p K810 -m -q "$f"
done
