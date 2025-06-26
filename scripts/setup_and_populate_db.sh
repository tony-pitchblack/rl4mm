#!/bin/bash

# Initialize micromamba if not already done
eval "$(micromamba shell hook --shell bash)"

# Activate the environment
micromamba activate rl4mm

echo "=== Setting up PostgreSQL database ==="

# Check if PostgreSQL is running
if ! pgrep -x "postgres" > /dev/null; then
    echo "Starting PostgreSQL..."
    sudo systemctl start postgresql
    sleep 2
fi

# Create admin user if not exists
echo "Setting up admin user..."
scripts/create_admin_user.sh

# Create database
echo "Creating database..."
scripts/create_db.sh

# Clear any existing data
echo "Clearing existing data..."
scripts/clear_db.sh

echo "=== Populating database with LOBSTER data ==="

# Populate database
scripts/populate_db.sh

echo "=== Database setup and population complete ==="
echo "You can connect to the database with: psql -h localhost -U admin -d lob_snapshots" 