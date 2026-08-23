# AI Retail Analytics Platform (ARAP)

## 1. Project Overview

ARAP is a computer vision platform that analyzes existing CCTV / IP camera
feeds to produce operational analytics for retail and coffee-shop
environments: person detection, multi-object tracking, customer counting,
dwell time, zone occupancy, entry/exit counting, staff activity analytics,
and more.

## 2. Project Goals

- Reuse existing CCTV infrastructure (RTSP / ONVIF) as the input source.
- Provide real-time and historical operational analytics.
- Keep the system modular: camera input, detection, tracking, zones,
  analytics, storage, and dashboard remain separate components.
- Deliver a real-time dashboard backed by FastAPI, PostgreSQL, and WebSocket.

## 3. Current Development Stage

**Sprint 13 — Forecasting + AI Analytics** (current). The backend now has a
daily time-series aggregation layer, feature engineering, baseline + linear
forecast models with chronological evaluation, correlation/conversion/anomaly
analytics, and deterministic AI insights. The dashboard shows a 7-day forecast
and AI analytics section.

> Deep learning, generative AI, autonomous decision-making, and production ML
> deployment are **NOT** implemented yet.

## 4. Architecture

```text
CCTV
 ↓
RTSP
 ↓
Video Processing
 ↓
YOLO
 ↓
Tracking
 ↓
Analytics
 ↓
FastAPI
 ↓
PostgreSQL
 ↓
Next.js Dashboard
```

## 5. Roadmap

```text
Sprint 1  Foundation
Sprint 2  CCTV / RTSP
Sprint 3  YOLO Detection
Sprint 4  Object Tracking
Sprint 5  Zone + Dwell Time
Sprint 6  FastAPI + PostgreSQL
Sprint 7  Next.js Dashboard
Sprint 8  Advanced Analytics + POS Integration
```

## 6. Project Structure

```text
ai-retail-analytics/
├── ai/            # computer vision package
│   ├── camera/    # RTSP/ONVIF camera input (Sprint 2)
│   ├── detection/ # YOLO person detection (Sprint 3)
│   ├── tracking/  # ByteTrack object tracking (Sprint 4)
│   └── analytics/ # zone + dwell time (Sprint 5)
├── backend/       # FastAPI application (Sprint 6)
├── frontend/      # Next.js dashboard (Sprint 7)
├── config/        # configuration files
├── data/          # local data (git-ignored content)
├── models/        # AI model weights (git-ignored)
├── recordings/    # camera recordings (git-ignored)
├── scripts/       # utility scripts
├── tests/         # test suite
├── docker/        # Docker files (future)
├── docs/          # documentation
├── .env.example
├── .gitignore
├── AGENTS.md
├── README.md
├── pyproject.toml
└── requirements.txt
```

## 7. Development Environment

- Windows 11 / VS Code / PowerShell
- Python 3.11+
- Node.js 22+ / npm
- Git
- Docker (used from later sprints)
- PostgreSQL 17 (used from Sprint 6)

## 8. Installation

```powershell
# Create the virtual environment (Python 3.11)
uv venv .venv --python 3.11

# Activate it
.venv\Scripts\Activate.ps1

# Install runtime dependencies (camera input)
uv pip install -r requirements.txt

# Install test dependencies
uv pip install -e ".[test]"
```

> The global `pip` on the development machine is broken (points to an older
> Python). Always install project dependencies through `.venv` using `uv`.

## 9. Testing

```powershell
# Run the test suite
.venv\Scripts\python.exe -m pytest
```

## 10. Git Workflow

- Small, logical commits with clear messages.
- Inspect `git status` / `git diff` before committing.
- Never commit `.env`, secrets, model weights, recordings, or generated caches.

## 11. Security Rules

- Never commit API keys, passwords, tokens, camera credentials, or database
  credentials.
- Never commit `.env` files (use `.env.example` as a template).
- Keep database access isolated from business logic.
- The frontend must communicate through documented APIs/WebSocket, never
  directly with the database.

## 12. Person Detection (Sprint 3)

The `ai.detection` package runs person detection on individual frames. It
accepts a `numpy.ndarray` frame (from a `CameraStream`, an image file, or any
other source) and returns a list of `Detection` objects.

```python
import cv2
from ai.detection import DetectionConfig, YOLODetector

config = DetectionConfig(
    model_path="models/yolov8n.pt",   # downloaded automatically on first use
    confidence_threshold=0.40,        # only keep detections >= this score
    device="cpu",                     # "cpu" or "cuda" if a GPU is available
)

detector = YOLODetector(config)
detector.load()

frame = cv2.imread("image.jpg")
detections = detector.detect(frame)

for d in detections:
    print(d.class_id, d.class_name, d.confidence, d.bbox.to_dict())
```

### Output format

Each `Detection` has `class_id`, `class_name`, `confidence`, and a `bbox`
(`x1`, `y1`, `x2`, `y2`). Sprint 3 returns only the `person` class (COCO id 0).

### Model

Uses a lightweight Ultralytics YOLO nano model (`yolov8n.pt`, ~6 MB). The
model is downloaded on first use into `models/` and is git-ignored. CPU is
the default device so development runs without a GPU; set `device="cuda"`
when a CUDA GPU is available.

## 13. Object Tracking (Sprint 4)

The `ai.tracking` package assigns temporary track ids to detections across
consecutive frames using a ByteTrack backend.

### Detection vs Tracking

- **Detection**: a person is detected on a single frame.
- **Tracking**: the same person keeps a temporary id across frames.

```python
from ai.tracking import ObjectTracker

tracker = ObjectTracker()

tracks_frame_1 = tracker.update(detections_frame_1)  # -> TrackResult(id=0, state=NEW)
tracks_frame_2 = tracker.update(detections_frame_2)  # -> TrackResult(id=0, state=ACTIVE)
```

Each `TrackResult` has `track_id`, `class_id`, `class_name`, `confidence`,
`bbox`, and a lifecycle `state` (`NEW`, `ACTIVE`, `LOST`, `REMOVED`).

### Important

A `track_id` is only a **temporary identity within a single tracking session**.
It is not a human identity and never encodes personal information.

## 14. Zone / ROI + Dwell Time (Sprint 5)

The `ai.analytics` package classifies tracks into zones and measures how long
each track stays in a zone.

### Coordinate system

Image coordinates: origin `(0, 0)` is the **top-left**, `x` grows to the right
and `y` grows downward. A track's position is its bounding-box **center point**
`(center_x, center_y)`.

### Zones and events

A `Zone` is a polygon (list of `[x, y]` vertices). The `ZoneEngine` emits an
`ENTER` event when a track's center enters a zone and an `EXIT` event when it
leaves — without repeating events every frame.

```python
from ai.analytics import Zone, ZoneEngine, DwellTimeAnalyzer

counter = Zone(zone_id="counter", name="Counter", polygon=[[100, 100], [500, 100], [500, 400], [100, 400]])
engine = ZoneEngine([counter])
dwell = DwellTimeAnalyzer()

zone_events = engine.update(tracks, timestamp)   # -> [ENTER/EXIT, ...]
dwell.update(zone_events)                         # starts/finishes sessions
```

### Dwell time

```
Track 17
  ENTER Counter: 10:00:00
  EXIT  Counter: 10:01:25
  Dwell: 85 seconds
```

Sessions are keyed by `(track_id, zone_id)`. Re-entering a zone starts a new
session (sessions are never merged). A `track_id` is only a temporary identity
and never identifies a real person.

## 15. FastAPI + PostgreSQL (Sprint 6)

The `backend` package exposes a REST API that ingests and queries retail
analytics. It follows a layered design so each concern stays isolated:

```text
Route handlers (backend/routers.py)   # HTTP only, no logic
        ↓
Services (backend/services.py)        # business rules
        ↓
Repositories (backend/repositories.py)  # data access only
        ↓
SQLAlchemy models (backend/models.py)   # PostgreSQL (or SQLite in tests)
```

### Configuration

`DATABASE_URL` selects the database. Production uses PostgreSQL; tests use
SQLite so the suite runs without a live server.

### Run the server

```powershell
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

### Endpoints

| Method | Path                | Description                         |
| ------ | ------------------- | ----------------------------------- |
| GET    | `/health`           | Liveness + database connectivity    |
| POST   | `/zones`            | Create a zone (polygon >= 3 points) |
| GET    | `/zones`            | List zones                          |
| POST   | `/events`           | Record ENTER/EXIT zone events       |
| POST   | `/dwell-sessions`   | Record completed dwell sessions     |
| GET    | `/analytics/dwell`  | Dwell sessions + per-zone summary   |

A dwell session's `duration` is derived server-side (`exit_time - enter_time`)
to keep a single source of truth. A `track_id` is a temporary identity only.

## 16. Next.js Dashboard (Sprint 7)

The `frontend` package is a Next.js (App Router) + TypeScript + Tailwind CSS
dashboard that consumes the FastAPI REST API. It is presentation-only: no SQL,
no PostgreSQL access, no YOLO/tracking/analytics code, and no business rules.

### Setup

```powershell
cd frontend
npm install
npm run dev          # http://localhost:3000
```

The dashboard expects the FastAPI backend to be running (Sprint 6). The API
base URL is configured via `NEXT_PUBLIC_API_BASE_URL` (see `frontend/.env.example`).

### Routes

| Path                  | Description                          |
| --------------------- | ------------------------------------ |
| `/dashboard`          | KPIs, dwell-by-zone chart, zone list |
| `/dashboard/zones`    | Zone list + create-zone form         |
| `/dashboard/dwell`    | Dwell sessions table + summary       |
| `/dashboard/events`   | Event test form (admin)              |

### Notes

- The Events page now lists events via `GET /events` (added in Sprint 8) and
  keeps an admin form that uses `POST /events`.
- Zone edit and enable/disable are supported via `PUT /zones/{id}` (Sprint 8).
  Disabling preserves historical analytics; zones are not hard-deleted.
- CORS in the backend allows `http://localhost:3000` by default and is
  configurable via `CORS_ORIGINS`.

### Checks

```powershell
npm run lint
npm run build
```

## 17. Advanced Retail Analytics (Sprint 8)

Sprint 8 completes the analytics API and adds first-level retail analytics.
Timestamps are Unix epoch seconds (UTC). Dwell sessions are either `ongoing`
(`exit_time`/`duration` are null) or `completed`.

### New/changed endpoints

| Method | Path                        | Description                                   |
| ------ | --------------------------- | --------------------------------------------- |
| GET    | `/events`                   | Paginated event list (`limit`, `offset`) + filters (`zone_id`, `event_type`, `track_id`, `start_time`, `end_time`) |
| PUT    | `/zones/{zone_id}`          | Update a zone's `name`, `polygon`, `enabled`  |
| GET    | `/analytics/dwell`          | Dwell sessions (ongoing + completed) with filters (`zone_id`, `track_id`, `status`, `start_time`, `end_time`, `min_duration`, `max_duration`) |
| GET    | `/analytics/summary`        | Totals + average/min/max dwell (time-range aware) |
| GET    | `/analytics/zones`          | Per-zone analytics (sessions, avg/total/max dwell) |
| GET    | `/analytics/daily`          | Daily dwell aggregation (UTC date)            |
| GET    | `/analytics/zones/ranking`  | Zone ranking by `average_dwell` (default) or `total_dwell` |

### Aggregation semantics

- Duration aggregates (`average_dwell_seconds`, `total_dwell_seconds`,
  `max_dwell_seconds`, `min_dwell_seconds`) are computed over **completed**
  sessions only; ongoing sessions contribute to counts
  (`ongoing_sessions`, `total_sessions`).
- `average_dwell_seconds`/`max_dwell_seconds`/`min_dwell_seconds` are `null`
  when no completed sessions exist (never `NaN`).
- For an ongoing session, `GET /analytics/dwell` reports `duration` as
  `now - enter_time` (a `now` query parameter is supported for deterministic
  reads; defaults to server time).

All aggregation runs database-side (SQLAlchemy `COUNT`/`AVG`/`SUM`/`MAX`/`MIN`);
business rules (duration derivation, ranking, filtering) live in the backend
service layer, never in the frontend.

## 18. Database Migrations + Hardening (Sprint 9)

The database schema is version-controlled with Alembic. Migrations are the
source of truth; the backend does **not** call `Base.metadata.create_all()` on
startup and never drops or recreates tables automatically.

### Configuration

- `alembic.ini` holds no credentials; `sqlalchemy.url` is resolved in
  `alembic/env.py` from the centralized `DATABASE_URL` setting (environment
  driven).
- `alembic/env.py` targets the real `backend.database.Base` metadata
  (`Zone`, `ZoneEvent`, `DwellSession`).

### Migration commands

```powershell
alembic upgrade head      # apply all migrations
alembic current           # show current revision
alembic history           # show migration chain
alembic downgrade -1      # undo the last migration (dev only)
alembic revision --autogenerate -m "message"   # generate a new revision (review it!)
```

### Development workflow

1. Configure `.env` (copy `.env.example`, set `DATABASE_URL`).
2. Start PostgreSQL.
3. Run `alembic upgrade head`.
4. Start FastAPI: `.venv\Scripts\python.exe -m uvicorn backend.main:app --reload`.
5. Start Next.js: `cd frontend; npm run dev`.

### Schema notes

- `zones.id` is the primary key (and the zone identifier); `polygon` stores the
  geometry as portable JSON (no PostGIS).
- `zone_events.timestamp`, `dwell_sessions.enter_time`/`exit_time` are Unix
  epoch seconds (UTC).
- `created_at` columns are timezone-aware (`timestamptz` on PostgreSQL).
- Indexes exist on `zone_events.(track_id, zone_id, event_type, timestamp)` and
  `dwell_sessions.(track_id, zone_id, enter_time, status)`.
- Ongoing dwell sessions keep `exit_time`/`duration` nullable (Sprint 8
  semantics preserved).

## 19. Real-Time WebSocket (Sprint 10)

The backend now streams live events over a WebSocket, and the dashboard
consumes them without polling.

```
Camera → Detection → Tracking → Zone/Dwell → Event Engine
                                                ├──→ PostgreSQL (persistence)
                                                └──→ Event Bus
                                                        ↓
                                               WebSocket Manager
                                                        ↓
                                               Next.js Dashboard
```

### Endpoint

- `GET /ws/events` — WebSocket endpoint (currently an internal endpoint; no
  authentication yet). No credentials are placed in the URL.

### Event envelope

All messages use a stable, versioned envelope:

```json
{"type": "zone_enter", "version": 1, "timestamp": 1234567890.0, "data": {"zone_id": "counter", "track_id": 7}}
```

Event types (shared vocabulary between backend and frontend):

`connection`, `heartbeat`, `detection`, `track_created`, `track_updated`,
`zone_enter`, `zone_exit`, `dwell_started`, `dwell_updated`, `dwell_completed`,
`analytics_update`, `system_status`.

Currently emitted on ingestion: `zone_enter`, `zone_exit`, `dwell_started`,
`dwell_completed`. The tracking/detection events are reserved for the live
camera pipeline (future sprint).

### Behavior

- Persistence (PostgreSQL) remains the source of truth; WebSocket is a
  delivery mechanism only.
- A background event bus decouples sync producers from the async WebSocket
  layer; WebSocket failures never break persistence or the REST API.
- A heartbeat is broadcast every `websocket_heartbeat_interval` seconds
  (default 30) and broken clients are dropped on send failure.
- The frontend `RealtimeClient` reconnects with bounded exponential backoff
  (1s → … → 30s cap), keeps a bounded 100-event buffer, and shows live
  connection status, counters, and an event feed on the dashboard.

### Security note

`/ws/events` is an internal, unauthenticated endpoint for now. The event bus is
structured so authentication can be added at the endpoint later without
changing producers or the connection manager.

### Tests

```powershell
.venv\Scripts\python.exe -m pytest           # incl. tests/test_realtime.py
cd frontend; npm run lint; npm run build
```

## 20. Multi-Camera Architecture (Sprint 11)

The platform now supports many cameras, each with an isolated pipeline. Every
event, zone, and dwell session is traceable to its `camera_id`.

```
┌───────────────┐
│ Camera Registry│
└───────┬───────┘
   ┌────┼────┐
 Camera 1  Camera N
   │          │
  RTSP       RTSP
   │          │
 YOLO       YOLO
   │          │
Tracking   Tracking
   │          │
Zone/Dwell Zone/Dwell
   └────┼────┘
        ↓
   Event Bus
   ┌───┴───┐
PostgreSQL  WebSocket → Dashboard
```

### Camera model

Cameras are stored in the `cameras` table and managed via REST. Fields:
`id`, `name`, `description`, `source_type` (`rtsp`/`onvif`/`file`/`test`),
`source_url`, `enabled`, `location`, `created_at`, `updated_at`. Credentials are
never stored in plaintext (they are resolved from environment, as in Sprint 2).

### Camera API

| Method | Path                         | Description                    |
| ------ | ---------------------------- | ------------------------------ |
| GET    | `/cameras`                   | List cameras                   |
| POST   | `/cameras`                   | Create a camera                |
| GET    | `/cameras/{id}`              | Get one camera                 |
| PUT    | `/cameras/{id}`              | Update a camera                |
| DELETE | `/cameras/{id}`              | Soft-delete (disable) a camera |
| GET    | `/cameras/{id}/status`       | Runtime status (in-memory)     |

### Track identity

A `track_id` is only meaningful within a single camera. The logical identity is
`(camera_id, track_id)`. Track IDs are **not** rewritten; events carry both
`camera_id` and `track_id`, so the same numeric track id on two cameras never
collides.

### Zone-camera relationship

A zone belongs to a camera (`zones.camera_id`). Zone events and dwell sessions
are denormalized with the zone's `camera_id` at ingest time, so historical
analytics stay correct even if a zone is later reassigned.

### Camera worker + test camera

- `backend/pipeline` defines `CameraSource` (with `TestCameraSource`), a
  `CameraWorker` that orchestrates source → detection → tracking → zone →
  dwell → events, and a `PipelineManager` that runs one isolated thread per
  camera. One camera's failure never stops another or the app.
- Runtime states: `unknown`, `starting`, `connected`, `running`,
  `reconnecting`, `disconnected`, `error`, `stopped`.
- RTSP reconnect is bounded (Sprint 2 `CameraStream`, 5s default interval).

### Real-time events

The event envelope now includes a top-level `camera_id` for camera-originated
events. Camera lifecycle events are emitted on the bus: `camera_connected`,
`camera_disconnected`, `camera_error`, `camera_reconnecting`.

### WebSocket camera filtering

Clients send subscription messages over `/ws/events`:

```json
{"type": "subscribe", "camera_ids": ["camera-01"]}   // empty list = all cameras
{"type": "unsubscribe", "camera_ids": ["camera-01"]}
```

The dashboard camera selector sends these subscriptions; selecting "All
Cameras" subscribes to everything.

### Analytics

All analytics endpoints (`/analytics/summary`, `/analytics/zones`,
`/analytics/daily`, `/analytics/zones/ranking`, `/analytics/dwell`,
`/events`) accept an optional `camera_id` filter. Existing filters remain
unchanged.

### Known limitations

- No live camera feed is wired in development: the worker pipeline is exercised
  via `TestCameraSource`; real RTSP/ONVIF/YOLO wiring is a follow-up.
- `camera_reconnecting` is defined but not yet emitted (RTSP reconnect runs
  inside `CameraStream`).
- Camera runtime status is in-memory (not persisted).

## 21. POS Integration Layer (Sprint 12)

A vendor-neutral POS integration layer ingests transactions, normalizes them,
enforces idempotency, persists them, and publishes transaction events to the
existing event bus / WebSocket.

```
POS → POS Adapter → Normalizer → Transaction Service
                                     ├──→ PostgreSQL
                                     └──→ EventBus → WebSocket → Dashboard
```

### POS adapter architecture

- `backend/pos/adapter.py` — `POSAdapter` interface (`health_check`,
  `fetch_transactions`).
- `backend/pos/normalizer.py` — `TransactionNormalizer` validates raw external
  data and derives line totals.
- `backend/pos/test_adapter.py` — `TestPOSAdapter` (deterministic, no external
  connection).

Adapters are never coupled to FastAPI routes. Future adapters (REST, webhook,
database, CSV, vendor SDK) implement `POSAdapter`.

### Transaction model

- `transactions`: `external_transaction_id`, `pos_source`, `store_id`,
  `terminal_id`, `transaction_time`, `subtotal`, `discount`, `tax`, `total`,
  `currency`, `payment_method`, `status`.
- `transaction_items`: `product_id`, `sku`, `product_name`, `quantity`,
  `unit_price`, `discount`, `tax`, `line_total` (nullable product/sku allowed).

### Idempotency

Ingestion is idempotent on `(pos_source, external_transaction_id)` (unique
constraint). Receiving the same transaction twice never creates a duplicate.

### Transaction statuses

`pending`, `completed`, `cancelled`, `refunded`. Cancellation/refund update
status only — historical records are never deleted.

### API

| Method | Path                            | Description                  |
| ------ | ------------------------------- | ---------------------------- |
| POST   | `/transactions/ingest`          | Ingest normalized transactions |
| GET    | `/transactions`                 | List (filters + pagination)  |
| GET    | `/transactions/summary`         | Aggregate analytics          |
| GET    | `/transactions/{id}`            | Transaction + items          |
| GET    | `/transactions/{id}/items`      | Line items                   |
| PATCH  | `/transactions/{id}/status`     | Cancel/refund/update status  |

Filters: `start_time`, `end_time`, `status`, `pos_source`, `payment_method`,
`terminal_id`, `limit`, `offset`.

### Analytics

`GET /transactions/summary` returns transaction count, gross/discount/tax/net
sales, average transaction value, items sold, and payment-method breakdown —
all aggregated database-side.

### Real-time events

New event types: `transaction_created`, `transaction_updated`,
`transaction_cancelled`, `transaction_refunded`. They flow through the existing
`/ws/events` endpoint (no separate endpoint). POS events carry no `camera_id`.

### Known limitations

- No per-person transaction correlation (no identity matching / facial
  recognition) — by design.
- No refund-line modeling: refunds are represented as a status change on the
  original transaction.
- POS ingestion endpoint is internal/unauthenticated (documented; auth deferred).

## 22. Forecasting + AI Analytics (Sprint 13)

A forecasting layer on top of the daily-aggregated data, plus deterministic
diagnostic analytics.

```
Camera + POS → Analytics → Features → Forecast → AI Insights
```

### Timezone policy

Event/dwell/transaction times are Unix epoch seconds (UTC). Daily aggregation
converts to a configurable business timezone (`analytics_timezone`, default
`UTC`) — never hard-coded into calculations.

### Daily aggregation

`backend/forecasting/aggregation.py` produces `DailyRecord`s (traffic, dwell,
transactions, sales, items) grouped by day. `traffic` is defined as the number
of zone-enter events (a camera-scopable visit count), NOT an identified-person
count.

### Feature engineering

Calendar features (day index, weekday) plus lag (`lag_1/7/14`) and rolling
(`rolling_7/14`) features — all computed from past values only (no leakage).

### Models

- Baselines: naive, seasonal naive, moving average.
- Model: linear regression over `[day index, weekday dummies]` (NumPy, no
  external ML dependency).

Models are evaluated **chronologically** (no random split) with MAE/RMSE/MAPE/
WAPE and compared honestly; the best (lowest MAE) is used for forecasting.

### API

| Method | Path                      | Description                    |
| ------ | ------------------------- | ------------------------------ |
| GET    | `/forecast`               | 7-day forecast (target, horizon, camera_id) |
| GET    | `/forecast/models`        | Available models               |
| GET    | `/forecast/evaluation`    | Chronological model comparison |
| POST   | `/forecast/refresh`       | Recompute + publish WS events  |
| GET    | `/analytics/trends`       | Recent vs previous trends      |
| GET    | `/analytics/correlations` | Traffic/sales/dwell correlation|
| GET    | `/analytics/anomalies`    | Rolling-window anomalies       |
| GET    | `/analytics/insights`     | Deterministic AI insights      |
| GET    | `/analytics/today`        | Authoritative "today" summary  |

Forecast targets: `traffic`, `transactions`, `net_sales`, `items_sold`,
`avg_transaction_value`. Insufficient history (< 21 days) returns
`insufficient_history` instead of meaningless predictions.

### Conversion metric

`transaction_rate_vs_traffic = transactions / traffic` — an operational ratio,
**not** person-level conversion (returns `null` when traffic is zero).

### Real-time events

`forecast_updated`, `analytics_insight`, `anomaly_detected` flow through the
existing `/ws/events` endpoint, published only on `/forecast/refresh`.

### Known limitations

- Forecasts are computed on demand from a small daily dataset (in-memory cache);
  no persistent model artifacts yet.
- Non-UTC timezone aggregation is approximate at the UTC-day boundary.
- Anomaly detection uses rolling mean/std (z-score); no advanced models.
