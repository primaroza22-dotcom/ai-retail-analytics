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

**Sprint 4 — Object Tracking** (current). The tracking subsystem
(`ai.tracking`) assigns temporary track ids to person detections across
frames using a ByteTrack backend, fully decoupled from the camera and
detector layers.

> Zone analytics, dwell time, and the dashboard are **NOT** implemented yet.
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
│   ├── camera/    # RTSP/ONVIF camera input (Sprint 2)
│   ├── detection/ # YOLO person detection (Sprint 3)
│   └── tracking/  # ByteTrack object tracking (Sprint 4)
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
