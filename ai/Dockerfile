FROM python:3.11-slim
WORKDIR /app

COPY pyproject.toml ./
COPY mirage_ai ./mirage_ai
COPY alembic.ini ./
COPY migrations ./migrations
COPY docker-entrypoint.sh ./

# The sed strips CRLF line endings picked up by Windows checkouts
# (core.autocrlf) — a CR after the shebang breaks exec with a misleading
# "no such file or directory".
RUN pip install --no-cache-dir -e . \
    && sed -i 's/\r$//' ./docker-entrypoint.sh \
    && chmod +x ./docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
