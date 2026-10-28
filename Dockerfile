FROM node:24.22.1-bookworm-slim@sha256:55fb5f5a527ea2c5c4a95f963e48ef90aa38c7b346054fdc8ee9957a2b55d205 AS web
WORKDIR /build/web
COPY web/package.json web/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --ignore-scripts --no-audit --no-fund
COPY web/src ./src
COPY web/index.html ./
COPY web/scripts/build.mjs ./scripts/build.mjs
RUN npm run build

FROM ghcr.io/astral-sh/uv:0.13.5@sha256:32a7bb39b496babbd997b0a39a4d66c126bdaf5661b302bf6f06abda8deca6ff AS uv
FROM python:3.14.9-slim-bookworm@sha256:945c2676dc2b18e0c1f16879244122c57c0ffede60006bf3df159c507a31bcae AS python-build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-install-project --python /usr/local/bin/python

FROM python:3.14.9-slim-bookworm@sha256:945c2676dc2b18e0c1f16879244122c57c0ffede60006bf3df159c507a31bcae
ARG FATA_RELEASE_VERSION=f4-01
LABEL org.opencontainers.image.version=$FATA_RELEASE_VERSION
ENV PATH=/app/.venv/bin:$PATH PYTHONPATH=/app/src PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    FATA_HOST=127.0.0.1 FATA_WORKERS=1 FATA_PROVIDER=fake FATA_TELEMETRY_EXPORTER=none \
    FATA_LOCAL_DEV=0 FATA_ENV=local
WORKDIR /app
COPY --from=python-build /app/.venv /app/.venv
COPY src ./src
COPY scripts/serve.py scripts/migrate.py scripts/release.py scripts/release_probe.py ./scripts/
COPY migrations ./migrations
COPY data/catalog ./data/catalog
COPY --from=web /build/web/dist ./web/dist
USER 10001:10001
STOPSIGNAL SIGTERM
ENTRYPOINT ["python", "scripts/release.py"]
CMD ["serve"]
