#!/usr/bin/env bash
set -euo pipefail

# If DATABASE_URL points to postgres, wait until it accepts connections.
if [[ "${DATABASE_URL:-}" == postgresql* ]]; then
    echo "Waiting for PostgreSQL..."
    until python - <<'EOF'
import os, sys
try:
    import psycopg2, urllib.parse as p
    u = p.urlparse(os.environ["DATABASE_URL"].replace("postgresql+psycopg2","postgresql"))
    psycopg2.connect(host=u.hostname, port=u.port or 5432,
                     dbname=u.path.lstrip("/"), user=u.username, password=u.password)
    sys.exit(0)
except Exception:
    sys.exit(1)
EOF
    do
        echo "  postgres not ready, retrying in 2s..."
        sleep 2
    done
    echo "PostgreSQL is ready."
fi

echo "Running alembic migrations..."
alembic upgrade head

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
