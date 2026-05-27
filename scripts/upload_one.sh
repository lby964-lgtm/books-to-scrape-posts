#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COUNT="${COUNT:-5}"
BRANCH="${BRANCH:-main}"
PYTHON_BIN="${PYTHON_BIN:-python}"
STATE_FILE="${STATE_FILE:-.upload_state}"
POST_DATE="${POST_DATE:-}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "This script must run inside a git repository." >&2
  exit 1
fi

if [ -z "$POST_DATE" ]; then
  first_post="$(git ls-files "posts/*.md" | sort | head -n 1 || true)"
  if [[ "$first_post" =~ posts/([0-9]{4}-[0-9]{2}-[0-9]{2})- ]]; then
    POST_DATE="${BASH_REMATCH[1]}"
  else
    POST_DATE="$(date +%F)"
  fi
fi

"$PYTHON_BIN" src/crawl_books.py --count "$COUNT" --output data/books.json
"$PYTHON_BIN" src/generate_markdown.py --input data/books.json --output-dir posts --date "$POST_DATE"

mapfile -t files < <(find posts -maxdepth 1 -type f -name "*.md" | sort | head -n "$COUNT")

if [ "${#files[@]}" -eq 0 ]; then
  echo "No Markdown posts were generated." >&2
  exit 1
fi

if [ -f "$STATE_FILE" ]; then
  uploaded="$(cat "$STATE_FILE")"
else
  uploaded="$(git ls-files "posts/*.md" | wc -l | tr -d " ")"
fi

next=$((uploaded + 1))

if [ "$next" -gt "$COUNT" ]; then
  echo "All $COUNT posts are already uploaded."
  exit 0
fi

file="${files[$((next - 1))]}"
title="$(grep -m 1 "^title:" "$file" | sed -E 's/^title:[[:space:]]*"?([^"]*)"?/\1/')"

git add "$file"

if git diff --cached --quiet; then
  echo "$next" > "$STATE_FILE"
  echo "Post $next already exists in git: $file"
  exit 0
fi

git commit -m "Add book post $next: $title"
git push origin "$BRANCH"

echo "$next" > "$STATE_FILE"
echo "Uploaded post $next: $file"
