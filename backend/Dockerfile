FROM python:3.11-slim
WORKDIR /app

COPY pyproject.toml requirements-lock.txt ./
COPY mirage_backend ./mirage_backend
COPY scripts ./scripts
COPY alembic.ini ./
COPY migrations ./migrations
COPY docker-entrypoint.sh ./

# The sed strips CRLF line endings picked up by Windows checkouts
# (core.autocrlf) — a CR after the shebang breaks exec with a misleading
# "no such file or directory". Dependencies install from the pinned
# lockfile first (reproducible build), then the local package itself
# with --no-deps so pip doesn't re-resolve against pyproject.toml's open
# ranges.
RUN pip install --no-cache-dir -r requirements-lock.txt \
    && pip install --no-cache-dir --no-deps -e . \
    && sed -i 's/\r$//' ./docker-entrypoint.sh \
    && chmod +x ./docker-entrypoint.sh

EXPOSE 8001
ENTRYPOINT ["./docker-entrypoint.sh"]
