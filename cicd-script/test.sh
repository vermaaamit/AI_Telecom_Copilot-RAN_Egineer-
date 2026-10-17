#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd -- "$script_dir/.." && pwd)"
backend_dir="$project_dir/ranengineer/backend"

if [ -f "$backend_dir/.venv/bin/pytest" ]; then
  cd "$backend_dir"
  "$backend_dir/.venv/bin/pytest"
elif command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -q "ranengineer-backend"; then
  docker exec ranengineer-backend-1 pytest
elif command -v pytest >/dev/null 2>&1; then
  cd "$backend_dir"
  pytest
elif command -v python3 >/dev/null 2>&1; then
  cd "$backend_dir"
  python3 -m pytest
else
  echo "No pytest execution environment found (checked .venv, docker, host pytest, and python3)." >&2
  exit 1
fi

