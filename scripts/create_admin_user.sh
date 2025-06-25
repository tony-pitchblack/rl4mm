#!/bin/bash

# Get current user's home directory
USER_HOME="$HOME"
PGPASS_FILE="$USER_HOME/.pgpass"

# First, we need to set a password for postgres user if not already set
echo "Setting up postgres user password..."
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';" 2>/dev/null || {
    echo "Failed to set postgres password. Make sure PostgreSQL is running."
    exit 1
}

# Create .pgpass file for password authentication
echo "localhost:5432:*:postgres:postgres" > "$PGPASS_FILE"
echo "localhost:5432:*:admin:admin" >> "$PGPASS_FILE"
chmod 600 "$PGPASS_FILE"

# Create admin user using TCP connection
psql -h localhost -U postgres -d postgres -c "
DO \$\$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles WHERE rolname = 'admin'
   ) THEN
      CREATE ROLE admin WITH LOGIN PASSWORD 'admin';
   END IF;
END
\$\$;"

echo "Admin user created successfully!"