#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd -- "$script_dir/.." && pwd)"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required for local deployment." >&2
  exit 1
fi

cd "$project_dir/ranengineer"
docker compose up --build -d
