#!/bin/sh
set -e

if [ -n "$DATABASE_URL_SYNC" ] && echo "$DATABASE_URL_SYNC" | grep -q "postgresql"; then
    echo "[entrypoint] 等待数据库就绪..."
    python - <<'PY'
import os
import socket
import time
from urllib.parse import urlparse

url = os.environ.get("DATABASE_URL_SYNC", "")
parsed = urlparse(url)
host = parsed.hostname or "postgres"
port = parsed.port or 5432

for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"[entrypoint] 数据库 {host}:{port} 已就绪")
            break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit(f"数据库 {host}:{port} 等待超时")
PY
fi

echo "[entrypoint] 初始化数据库..."
python init_db.py

echo "[entrypoint] 启动应用: $*"
exec "$@"
