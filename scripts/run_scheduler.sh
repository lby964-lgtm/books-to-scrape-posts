#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COUNT="${COUNT:-5}"
INTERVAL_SECONDS="${INTERVAL_SECONDS:-300}"
STATE_FILE="${STATE_FILE:-.upload_state}"

current_state() {
  if [ -f "$STATE_FILE" ]; then
    cat "$STATE_FILE"
  else
    git ls-files "posts/*.md" | wc -l | tr -d " "
  fi
}

while true; do
  bash scripts/upload_one.sh

  uploaded="$(current_state)"
  if [ "$uploaded" -ge "$COUNT" ]; then
    echo "Scheduled upload finished: $uploaded/$COUNT posts uploaded."
    break
  fi

  echo "Waiting $INTERVAL_SECONDS seconds before the next upload..."
  sleep "$INTERVAL_SECONDS"
done
