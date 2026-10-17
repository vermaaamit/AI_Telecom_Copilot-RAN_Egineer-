#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd -- "$script_dir/.." && pwd)"
frontend_dir="$project_dir/ranengineer/frontend"

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required to build the frontend." >&2
  exit 1
fi

cd "$frontend_dir"
if [[ -f package-lock.json ]]; then
  npm ci
else
  npm install
fi
npm run build
