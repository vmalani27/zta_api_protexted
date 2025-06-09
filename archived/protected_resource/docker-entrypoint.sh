#!/bin/bash
set -e

# Start PostgreSQL
service postgresql start

# Wait for PostgreSQL to be ready
until pg_isready -h localhost -p 5432 -U postgres; do
    echo "Waiting for PostgreSQL to be ready..."
    sleep 1
done

# Change to the application directory
cd /protected-resource

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 