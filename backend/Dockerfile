FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /usr/local/bin/uv

# The environment lives outside /app: Compose bind-mounts ./backend over
# /app for live reload, which would hide a /app/.venv (and expose the
# host's, built for a different OS).
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Dependencies first, from the lockfile, so code changes don't invalidate
# this layer. The app itself runs from /app and isn't installed.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY alembic.ini entrypoint.sh ./
COPY app ./app
COPY alembic ./alembic
COPY scripts ./scripts

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
