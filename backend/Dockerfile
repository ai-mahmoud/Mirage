FROM python:3.11-slim
WORKDIR /app

COPY pyproject.toml ./
COPY mirage_backend ./mirage_backend
COPY scripts ./scripts
COPY docker-entrypoint.sh ./

RUN pip install --no-cache-dir -e . \
    && chmod +x ./docker-entrypoint.sh

EXPOSE 8001
ENTRYPOINT ["./docker-entrypoint.sh"]
