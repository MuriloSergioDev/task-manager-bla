FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml alembic.ini entrypoint.sh ./
COPY app ./app
COPY alembic ./alembic
COPY scripts ./scripts

RUN pip install --no-cache-dir -e . \
    && chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
