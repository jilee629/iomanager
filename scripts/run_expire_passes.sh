#!/usr/bin/env bash
set -euo pipefail
cd /home/ubuntu/iomanager
if command -v uv >/dev/null 2>&1; then
  /usr/bin/env uv run python manage.py expire_passes >> /home/ubuntu/iomanager/logs/expire_passes.log 2>&1
else
  /usr/bin/env python3 manage.py expire_passes >> /home/ubuntu/iomanager/logs/expire_passes.log 2>&1
fi
