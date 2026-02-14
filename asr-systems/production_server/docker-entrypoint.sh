#!/bin/sh
set -e

cd /app

# Run Alembic migrations before starting the application
echo "Running database migrations..."
python -m alembic upgrade head
echo "Migrations complete."

# Execute the original CMD
exec "$@"
