#!/bin/bash

# Initialize micromamba if not already done
eval "$(micromamba shell hook --shell bash)"

# Activate the environment
micromamba activate rl4mm

echo "Clearing all data from the database..."
psql -h localhost -U admin -d lob_snapshots -c "TRUNCATE TABLE book, messages CASCADE;"

echo "Database cleared successfully!"