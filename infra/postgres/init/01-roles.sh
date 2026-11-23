#!/bin/sh
# Runs once, on first initialisation of the Postgres data volume.
# POSTGRES_USER (the owner role) and POSTGRES_DB are created by the image itself.
#
# Layout:
#   public    auth and RBAC tables (owned by Django). The agent role has NO access here.
#   datasets  data the agent may query. The agent role has SELECT only, here only.
#
# Passwords come from the environment.
set -eu

: "${POSTGRES_READONLY_USER:?POSTGRES_READONLY_USER is required}"
: "${POSTGRES_READONLY_PASSWORD:?POSTGRES_READONLY_PASSWORD is required}"

psql -v ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v owner="$POSTGRES_USER" \
  -v db="$POSTGRES_DB" \
  -v ro_user="$POSTGRES_READONLY_USER" \
  -v ro_pass="$POSTGRES_READONLY_PASSWORD" <<'SQL'
-- Read-only role: can log in and SELECT from the datasets schema, nothing else.
CREATE ROLE :"ro_user" LOGIN PASSWORD :'ro_pass'
  NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;

-- Guardrails for agent queries.
ALTER ROLE :"ro_user" SET statement_timeout = '5s';
ALTER ROLE :"ro_user" SET default_transaction_read_only = on;
ALTER ROLE :"ro_user" SET search_path = datasets;

-- Lock down the database and the public schema (auth and RBAC live there).
REVOKE ALL ON DATABASE :"db" FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE :"db" TO :"ro_user";

-- Schema for agent-queryable data, owned by the owner role.
CREATE SCHEMA datasets AUTHORIZATION :"owner";
GRANT USAGE ON SCHEMA datasets TO :"ro_user";
GRANT SELECT ON ALL TABLES IN SCHEMA datasets TO :"ro_user";

-- Tables the owner creates in datasets later are readable by the agent automatically.
ALTER DEFAULT PRIVILEGES FOR ROLE :"owner" IN SCHEMA datasets
  GRANT SELECT ON TABLES TO :"ro_user";
SQL
