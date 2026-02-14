#!/bin/sh
set -e

cd /app

# Run Alembic migrations with PostgreSQL advisory lock to prevent race conditions
# when multiple ECS tasks start simultaneously.
# Lock ID 1 is reserved for Alembic migrations.
echo "Running database migrations..."
python -c "
import os, sys
db_url = os.environ.get('DATABASE_URL', '')
if 'postgresql' in db_url:
    from sqlalchemy import create_engine, text
    engine = create_engine(db_url)
    with engine.connect() as conn:
        # Acquire advisory lock (blocks until available, released on disconnect)
        conn.execute(text('SELECT pg_advisory_lock(1)'))
        try:
            from alembic.config import Config
            from alembic import command
            alembic_cfg = Config('alembic.ini')
            command.upgrade(alembic_cfg, 'head')
        finally:
            conn.execute(text('SELECT pg_advisory_unlock(1)'))
            conn.commit()
    engine.dispose()
    print('Migrations complete (with advisory lock).')
else:
    # SQLite or no DB — run alembic directly (no locking needed)
    import subprocess
    subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], check=True)
    print('Migrations complete.')
"

# Execute the original CMD
exec "$@"
