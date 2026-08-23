# ARAP — Deployment Guide

Production deployment for the AI Retail Analytics Platform (ARAP).

> This guide prepares a production deployment package. No deployment has been
> executed to an external server, and no production database has been created.

## 1. Prerequisites

- Python 3.11+ (backend)
- Node.js 22+ / npm (frontend)
- PostgreSQL 17 (production database)
- Docker + Docker Compose (optional, containerized deployment)

## 2. Environment variables

Copy `.env.example` to `.env` (never commit `.env`). Key variables:

| Variable                         | Purpose                                      |
| -------------------------------- | -------------------------------------------- |
| `APP_ENV`                        | `development` / `test` / `production`        |
| `APP_DEBUG`                      | `true` in dev, `false` in production         |
| `LOG_LEVEL`                      | `DEBUG` / `INFO` / `WARNING` / `ERROR`       |
| `DATABASE_URL`                   | `postgresql+psycopg://user:pass@host:5432/arap` |
| `DATABASE_POOL_SIZE`             | Connection pool size (default 5)             |
| `DATABASE_POOL_MAX_OVERFLOW`     | Pool max overflow (default 10)               |
| `DATABASE_POOL_TIMEOUT`          | Pool acquire timeout seconds (default 30)    |
| `CORS_ORIGINS`                   | JSON list of allowed origins                 |
| `ANALYTICS_TIMEZONE`             | IANA business timezone (default `UTC`)       |
| `WEBSOCKET_HEARTBEAT_INTERVAL`   | WebSocket keepalive seconds (default 30)     |
| `CAMERA_PASSWORD`                | Camera credential (referenced via `password_env`) |

Secrets (`DATABASE_URL` password, `CAMERA_PASSWORD`, `DEEPSEEK_API_KEY`) must
never be committed.

## 3. Configuration matrix

|                | DEV        | TEST       | PROD            |
| -------------- | ---------- | ---------- | --------------- |
| Database       | SQLite     | SQLite     | PostgreSQL      |
| Debug          | ON         | OFF        | OFF             |
| Reload         | ON         | OFF        | OFF             |
| CORS           | localhost  | test       | restricted      |
| Logging        | DEBUG      | INFO       | INFO            |
| Camera source  | test       | test       | real RTSP/ONVIF |
| POS            | test       | test       | real adapter    |
| WebSocket      | yes        | yes        | yes             |
| Forecast       | yes        | yes        | yes             |

## 4. Database setup

Alembic is the ONLY source of truth for the production schema. The application
never calls `Base.metadata.create_all()` on startup.

```powershell
alembic upgrade head      # apply all migrations
alembic current           # show current revision
alembic history           # show migration chain
```

Never run `drop`/`recreate` against production.

## 5. Backend

```powershell
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Critical:** run a **single** uvicorn worker. Camera workers are in-process
(one thread per camera); multiple workers would duplicate camera pipelines.

## 6. Frontend

```powershell
cd frontend
npm install
npm run build
npm start             # serve the production build (port 3000)
```

Set `NEXT_PUBLIC_API_BASE_URL` to the backend origin (http and https are
mapped to ws/wss automatically by the realtime client).

## 7. Docker deployment

```powershell
$env:POSTGRES_PASSWORD = "change-me"
docker compose up --build
```

Services: `postgres` (with `pgdata` volume), `backend` (runs
`alembic upgrade head` then uvicorn), `frontend` (production Next.js build).

For an external PostgreSQL server, omit the `postgres` service and set
`DATABASE_URL` directly on the backend.

## 8. Reverse proxy + WebSocket

The `/ws/events` endpoint must support the WebSocket upgrade. Example nginx
directives:

```nginx
location / {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

TLS is NOT configured by this repository; terminate TLS at the proxy with
certificates you provision.

## 9. Health checks

| Endpoint   | Type      | Description                              |
| ---------- | --------- | ---------------------------------------- |
| `GET /health`  | Liveness  | Process is up (200)                  |
| `GET /ready`   | Readiness | Database reachable (200 / 503)       |
| `GET /version` | Info      | App name + version                   |
| `GET /status`  | Metrics   | DB status, WS clients, camera states |

## 10. Logging

The backend logs structured lines to stdout (level from `LOG_LEVEL`). In
containers, stdout is captured by the orchestrator; configure log rotation /
retention at the container/orchestrator level. Never log secrets or full
sensitive payloads, and never per-frame camera logs.

## 11. Backup strategy (PostgreSQL)

Logical backup (no automated tooling is wired in this repo yet):

```powershell
pg_dump -Fc -h $DB_HOST -U $DB_USER $DB_NAME > arap_$(Get-Date -Format yyyyMMdd).dump
```

Restore:

```powershell
pg_restore -h $DB_HOST -U $DB_USER -d $DB_NAME --clean --if-exists arap_YYYYMMDD.dump
```

Recommendations: daily backups, 30-day retention, periodic restore testing, and
offsite backup storage. **Backups are not operational until configured.**

## 12. Recovery sequence

1. Ensure PostgreSQL is available.
2. Restore backup if required (see above).
3. Set `DATABASE_URL`.
4. `alembic upgrade head`.
5. Start the backend.
6. Verify `GET /ready` returns 200.
7. Verify the dashboard loads.
8. Verify `GET /status` shows `database: connected`.
9. Verify WebSocket connectivity.
10. Verify camera workers / POS ingestion.

## 13. Rollback strategy

**Application rollback** (code) and **database migration rollback** (schema) are
different and must be handled separately:

- **Application rollback** — redeploy the previous image/commit. Do NOT
  automatically downgrade migrations.
- **Migration rollback** — an explicit, reviewed `alembic downgrade -1` only,
  never as part of an app redeploy.

## 14. Security limitations

- `/ws/events` is currently internal/unauthenticated.
- `POST /transactions/ingest` is currently internal/unauthenticated; it must be
  placed behind a trusted network or an authentication gateway.
- Rate limiting is NOT built-in; integrate a reverse proxy / API gateway for
  `/transactions/ingest`, `/ws/events`, and `/forecast/refresh`.
- CORS is configurable; never use `*` with authenticated requests.
- No TLS is provisioned by this repository.

## 15. Resource limits

| Resource               | Default        |
| ---------------------- | -------------- |
| Camera workers         | one thread per enabled camera |
| WebSocket heartbeat    | 30s            |
| WebSocket event buffer (frontend) | 100 (camera) / 50 (POS) |
| API pagination limit   | 500            |
| Forecast horizon       | 1–30 days      |
| DB pool                | 5 + 10 overflow |
| POS ingestion payload  | unbounded (add a proxy limit) |

## 16. Troubleshooting

- `/ready` returns 503 → check `DATABASE_URL` and PostgreSQL connectivity.
- WebSocket disconnects → verify the proxy forwards the `Upgrade` header.
- Camera workers not running → verify `enabled` camera records and RTSP reach.
- Forecast `insufficient_history` → fewer than 21 days of data.
