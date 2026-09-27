#!/bin/bash
# Runs automatically on first container init (empty data dir only), via
# Postgres's docker-entrypoint-initdb.d convention. Creates the second
# database integration tests run against (see backend/tests/conftest.py
# and README's "Database" section) alongside the main one, so a fresh
# `docker compose up` needs no manual `CREATE DATABASE` step.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE taskdb_test;
EOSQL
