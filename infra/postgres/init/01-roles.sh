#!/bin/sh
# Runs once, on first initialisation of the Postgres data volume.
# POSTGRES_USER (the owner role) and POSTGRES_DB are created by the image itself.
# This script adds a SELECT-only role for the agent. Passwords come from the environment.
set -eu

: "${POSTGRES_READONLY_USER:?POSTGRES_READONLY_USER is required}"
: "${POSTGRES_READONLY_PASSWORD:?POSTGRES_READONLY_PASSWORD is required}"

psql -v ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v owner="$POSTGRES_USER" \
  -v db="$POSTGRES_DB" \
  -v ro_user="$POSTGRES_READONLY_USER" \
  -v ro_pass="$POSTGRES_READONLY_PASSWORD" <<'SQL'
-- Read-only role: can log in and SELECT, nothing else.
CREATE ROLE :"ro_user" LOGIN PASSWORD :'ro_pass'
  NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;

-- Guardrails for agent queries.
ALTER ROLE :"ro_user" SET statement_timeout = '5s';
ALTER ROLE :"ro_user" SET default_transaction_read_only = on;

-- Nobody but the owner may create objects in the public schema.
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE :"db" FROM PUBLIC;

GRANT CONNECT ON DATABASE :"db" TO :"ro_user";
GRANT USAGE ON SCHEMA public TO :"ro_user";
GRANT SELECT ON ALL TABLES IN SCHEMA public TO :"ro_user";

-- Tables the owner creates later (via Django migrations) are readable automatically.
ALTER DEFAULT PRIVILEGES FOR ROLE :"owner" IN SCHEMA public
  GRANT SELECT ON TABLES TO :"ro_user";
SQL
