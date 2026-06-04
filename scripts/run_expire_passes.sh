#!/usr/bin/env bash
set -euo pipefail
cd /home/ubuntu/iomanager
echo "--- Execution started at: $(date '+%Y-%m-%d %H:%M:%S') ---" >> /home/ubuntu/iomanager/logs/expire_passes.log
/home/ubuntu/iomanager/.venv/bin/python manage.py expire_passes >> /home/ubuntu/iomanager/logs/expire_passes.log 2>&1
