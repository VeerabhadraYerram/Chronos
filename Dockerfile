FROM node:20.19.6-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_PUBLIC_EVALUATION=1
RUN npm test && npm run build

FROM falkordb/falkordb:v4.22.1@sha256:b0bdcac2cbaff989e77cb0610439b7a9289e86de033ccbbd4368b66fb680ae7a AS graph

FROM python:3.13-slim-trixie
ENV FALKOR_SOCKET_TIMEOUT_SECONDS=30 FALKOR_READ_TIMEOUT_MS=10000 FALKOR_WRITE_TIMEOUT_MS=10000
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend CHRONOS_STATIC_DIR=/app/frontend/dist
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 libstdc++6 libsystemd0 libcap2 libzstd1 && rm -rf /var/lib/apt/lists/*
COPY --from=graph /usr/local/bin/redis-server /usr/local/bin/redis-server
COPY --from=graph /var/lib/falkordb/bin/falkordb.so /usr/local/lib/falkordb.so
COPY backend/requirements.lock.txt ./requirements.lock.txt
RUN pip install --no-cache-dir -r requirements.lock.txt && useradd --create-home chronos
COPY --chown=chronos:chronos backend/chronos ./backend/chronos
COPY --chown=chronos:chronos deploy/start-evaluation.py deploy/build-reference.py ./deploy/
RUN python /app/deploy/build-reference.py && chown -R chronos:chronos /app/reference
COPY --from=frontend --chown=chronos:chronos /build/dist ./frontend/dist
USER chronos
EXPOSE 8000
CMD ["python", "/app/deploy/start-evaluation.py"]
