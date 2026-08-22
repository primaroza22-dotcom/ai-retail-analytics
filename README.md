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

**Sprint 2 — CCTV / RTSP / ONVIF** (current). The camera input subsystem
(`ai.camera`) provides camera configuration, RTSP frame capture with
automatic reconnect, multi-camera management, and an ONVIF foundation.

> YOLO, tracking, analytics, and the dashboard are **NOT** implemented yet.
> They will be built in later sprints.

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
│   └── camera/    # RTSP/ONVIF camera input (Sprint 2)
├── backend/       # FastAPI application (future)
├── frontend/      # Next.js dashboard (future)
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
