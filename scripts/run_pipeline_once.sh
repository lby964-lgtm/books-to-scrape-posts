#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COUNT="${COUNT:-5}"
PYTHON_BIN="${PYTHON_BIN:-python}"
POST_DATE="${POST_DATE:-$(date +%F)}"

"$PYTHON_BIN" src/crawl_books.py --count "$COUNT" --output data/books.json
"$PYTHON_BIN" src/generate_markdown.py --input data/books.json --output-dir posts --date "$POST_DATE"
