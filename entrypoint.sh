#!/bin/sh

set -e

MODE=${KCC_MODE:-c2e}

case "$MODE" in
  "c2e")
    echo "Starting C2E..."
    exec c2e "$@"
    ;;

  "c2p")
    echo "Starting C2P..."
    exec c2p "$@"
    ;;

  *)
    echo "Error: Unknown mode '$MODE'" >&2
    exit 1
    ;;
esac