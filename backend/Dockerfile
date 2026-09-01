FROM python:3.13-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/pyproject.toml
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic
COPY app /app/app
COPY entrypoint.sh /app/entrypoint.sh
RUN pip install --no-cache-dir . && chmod +x /app/entrypoint.sh

ENV PYTHONUNBUFFERED=1
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
