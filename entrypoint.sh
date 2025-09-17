#!/bin/bash
set -ex

# Wait for the PostgreSQL database to be ready
echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h db -p 5432 -U user; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL is up - executing command"

# Create RDKit extension
echo "Creating RDKit extension..."
PGPASSWORD=password psql -h db -p 5432 -U user -d chemstructdb -c "CREATE EXTENSION IF NOT EXISTS rdkit;"

# Run Alembic migrations
echo "Running Alembic migrations..."
alembic upgrade head

# Start the FastAPI application
echo "Starting FastAPI application..."
exec uvicorn src.app.main:app --host 0.0.0.0 --port 8000
