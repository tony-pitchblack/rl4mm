#!/bin/bash

# Check if .pgpass exists (should be created by create_admin_user.sh first)
PGPASS_FILE="$HOME/.pgpass"
if [ ! -f "$PGPASS_FILE" ]; then
    echo "Error: .pgpass file not found. Please run create_admin_user.sh first."
    exit 1
fi

echo "Creating lob_snapshots database..."

# Disconnect all users from lob_snapshots
psql -h localhost -U postgres -d postgres -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'lob_snapshots' AND pid <> pg_backend_pid();
" 2>/dev/null

# Drop and recreate the DB
psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS lob_snapshots;" || {
    echo "Failed to drop database (this is OK if it doesn't exist)"
}

if ! psql -h localhost -U postgres -c "CREATE DATABASE lob_snapshots;"; then
    echo "Failed to create database"
    exit 1
fi

echo "Database created successfully. Setting up permissions..."

# Give ownership of schema
psql -h localhost -U postgres -d lob_snapshots -c "ALTER SCHEMA public OWNER TO admin;"

# Grant all privileges on DB level
psql -h localhost -U postgres -d lob_snapshots -c "GRANT ALL PRIVILEGES ON DATABASE lob_snapshots TO admin;"
psql -h localhost -U postgres -d lob_snapshots -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;"
psql -h localhost -U postgres -d lob_snapshots -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO admin;"

echo "Database setup completed successfully!"
echo "You can now connect as admin user: psql -h localhost -U admin -d lob_snapshots"
