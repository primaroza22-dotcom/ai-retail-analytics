# AI Retail Analytics Platform

## Tujuan

Sistem computer vision untuk retail/coffee shop yang menggunakan CCTV existing untuk menghasilkan operational analytics.

## Roadmap

```text
Sprint 1  Foundation
Sprint 2  CCTV / RTSP
Sprint 3  YOLO Detection
Sprint 4  Object Tracking
Sprint 5  Zone + Dwell Time
Sprint 6  FastAPI + PostgreSQL
Sprint 7  Next.js Dashboard
Sprint 8  Advanced Analytics
```

## Architecture

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

> Sprint 1 belum mengimplementasikan pipeline di atas. Sprint 1 hanya menyiapkan
> fondasi proyek: struktur direktori, environment Python, konfigurasi, dan
> pengujian dasar.

## Status Saat Ini (Sprint 1 — Foundation)

- Struktur proyek modular (`ai/`, `backend/`, `frontend/`, dll.)
- Virtual environment Python 3.11 (`uv venv .venv`)
- `pyproject.toml` modern dengan konfigurasi `pytest`
- `requirements.txt` minimal (belum ada dependency AI)
- `.env.example` dan `.gitignore`
- Aturan agent (`AGENTS.md`)
- Pengujian dasar (`tests/test_project.py`)

## Setup Development

```powershell
# Buat virtual environment (Python 3.11)
uv venv .venv --python 3.11

# Aktifkan
.venv\Scripts\Activate.ps1

# Install test dependencies
uv pip install -e ".[test]"

# Jalankan test
uv run pytest
```
