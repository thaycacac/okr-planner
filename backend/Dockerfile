FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
RUN pip install .

RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000
# Proxy headers are handled by the app (TRUSTED_PROXY_IPS), so uvicorn must not rewrite the client.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --no-proxy-headers"]
