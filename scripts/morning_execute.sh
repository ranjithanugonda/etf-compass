#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
echo "Running morning execute at $(date '+%Y-%m-%d %H:%M:%S') IST"
python -m backend.app.jobs.morning_execute
