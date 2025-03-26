# Disconnect all users from lob_snapshots
psql -U postgres -d postgres -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'lob_snapshots' AND pid <> pg_backend_pid();
"
# Drop and recreate the DB
psql -U postgres -c "DROP DATABASE IF EXISTS lob_snapshots;"
psql -U postgres -c "CREATE DATABASE lob_snapshots;"

# Give ownership of schema
psql -U postgres -d lob_snapshots -c "ALTER SCHEMA public OWNER TO admin;"

# (Optional) Also grant all on DB level
psql -U postgres -d lob_snapshots -c "GRANT ALL PRIVILEGES ON DATABASE lob_snapshots TO admin;"
