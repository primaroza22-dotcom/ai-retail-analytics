"""Tests for camera configuration models and persistence."""

from pathlib import Path

import pytest

from ai.camera.config import CameraConfig, CameraConfigStore
from ai.camera.exceptions import CameraConfigError


def make_config(**overrides) -> CameraConfig:
    data = {
        "id": "cam-1",
        "name": "Entrance",
        "rtsp_url": "rtsp://10.0.0.10:554/stream1",
    }
    data.update(overrides)
    return CameraConfig(**data)


def test_config_requires_id_and_rtsp_url() -> None:
    with pytest.raises(CameraConfigError):
        CameraConfig(id="", name="x", rtsp_url="rtsp://x")
    with pytest.raises(CameraConfigError):
        CameraConfig(id="cam", name="x", rtsp_url="")


def test_config_round_trip_to_from_dict() -> None:
    cfg = make_config(password="secret", width=1920, height=1080)
    assert CameraConfig.from_dict(cfg.to_dict()) == cfg


def test_config_redact_masks_password_only() -> None:
    cfg = make_config(username="admin", password="secret")
    data = cfg.to_dict(redact_secrets=True)
    assert data["password"] == "********"
    assert data["username"] == "admin"


def test_password_resolved_prefers_in_memory() -> None:
    cfg = make_config(password="mem", password_env="CAM_PASS")
    assert cfg.password_resolved == "mem"


def test_password_resolved_falls_back_to_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAM_PASS", "from-env")
    cfg = make_config(password_env="CAM_PASS")
    assert cfg.password_resolved == "from-env"


def test_password_resolved_none_when_unset() -> None:
    assert make_config().password_resolved is None


def test_store_save_never_writes_plaintext_password(tmp_path: Path) -> None:
    path = tmp_path / "cameras.json"
    CameraConfigStore(path).save([make_config(password="top-secret")])
    assert "top-secret" not in path.read_text(encoding="utf-8")


def test_store_round_trip_preserves_env_reference(tmp_path: Path) -> None:
    path = tmp_path / "cameras.json"
    CameraConfigStore(path).save([make_config(password_env="CAM_PASS")])
    loaded = CameraConfigStore(path).load()
    assert len(loaded) == 1
    assert loaded[0].password_env == "CAM_PASS"
    assert loaded[0].password is None


def test_store_load_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(CameraConfigError):
        CameraConfigStore(tmp_path / "nope.json").load()


def test_store_ignores_unknown_fields(tmp_path: Path) -> None:
    path = tmp_path / "cameras.json"
    path.write_text(
        '{"cameras": [{"id": "c", "name": "n", "rtsp_url": "rtsp://x", "future_field": 1}]}',
        encoding="utf-8",
    )
    loaded = CameraConfigStore(path).load()
    assert loaded[0].id == "c"
