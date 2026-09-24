#!/bin/sh
set -e

# Postgres readiness is already guaranteed by docker-compose's
# depends_on: condition: service_healthy, so this only needs to migrate.
alembic upgrade head

exec "$@"
