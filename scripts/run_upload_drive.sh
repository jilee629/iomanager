#!/usr/bin/env bash
set -euo pipefail
cd /home/ubuntu/iomanager
echo "--- Execution started at: $(date '+%Y-%m-%d %H:%M:%S') ---" >> /home/ubuntu/iomanager/logs/upload_drive.log
/home/ubuntu/iomanager/.venv/bin/python scripts/upload_drive.py >> /home/ubuntu/iomanager/logs/upload_drive.log 2>&1
