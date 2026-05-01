#!/usr/bin/env bash
set -euo pipefail
cd /home/ubuntu/iomanager
echo "--- Execution started at: $(date '+%Y-%m-%d %H:%M:%S') ---" >> /home/ubuntu/iomanager/logs/upload_drive.log
if command -v uv >/dev/null 2>&1; then
  /usr/bin/env uv run python scripts/upload_drive.py >> /home/ubuntu/iomanager/logs/upload_drive.log 2>&1
else
  /usr/bin/env python3 scripts/upload_drive.py >> /home/ubuntu/iomanager/logs/upload_drive.log 2>&1
fi