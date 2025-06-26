#!/bin/bash

# Initialize micromamba if not already done
eval "$(micromamba shell hook --shell bash)"

# Activate the environment
micromamba activate rl4mm

echo "=== Database Connection Test ==="

# Test connection
if psql -h localhost -U admin -d lob_snapshots -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✓ Database connection successful"
else
    echo "✗ Database connection failed"
    exit 1
fi

# Show table counts
echo ""
echo "=== Table Counts ==="
psql -h localhost -U admin -d lob_snapshots -c "
SELECT 
    'book' as table_name, COUNT(*) as row_count 
FROM book
UNION ALL
SELECT 
    'messages' as table_name, COUNT(*) as row_count 
FROM messages;
"

# Show sample data
echo ""
echo "=== Sample Book Data ==="
psql -h localhost -U admin -d lob_snapshots -c "
SELECT ticker, timestamp, exchange 
FROM book 
ORDER BY timestamp 
LIMIT 3;
"

echo ""
echo "=== Sample Message Data ==="
psql -h localhost -U admin -d lob_snapshots -c "
SELECT ticker, timestamp, message_type, direction, price 
FROM messages 
ORDER BY timestamp 
LIMIT 5;
" 