set -euo pipefail
cd /home/ubuntu/iomanager
if command -v uv >/dev/null 2>&1; then
  /usr/bin/env uv run python scripts/upload_db.py >> /home/ubuntu/iomanager/logs/upload_db.log 2>&1
else
  /usr/bin/env python3 scripts/upload_db.py >> /home/ubuntu/iomanager/logs/upload_db.log 2>&1
fi