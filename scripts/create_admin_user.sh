psql -U postgres -d postgres -c "
DO \$\$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles WHERE rolname = 'admin'
   ) THEN
      CREATE ROLE admin WITH LOGIN PASSWORD 'admin';
   END IF;
END
\$\$;"
chmod 600 /home/admin/.pgpass