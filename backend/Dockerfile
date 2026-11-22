# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder
ENV POETRY_VERSION=2.5.2 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root

FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"
RUN groupadd --system app && useradd --system --gid app --home /app app
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --chown=app:app . .
USER app
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
