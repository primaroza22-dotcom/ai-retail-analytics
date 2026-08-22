"""Tests for the ONVIF foundation and RTSP URL construction."""

from ai.camera.onvif import OnvifClient, OnvifDeviceInfo, build_rtsp_url


class FakeOnvifClient(OnvifClient):
    def get_device_information(self) -> OnvifDeviceInfo:
        return OnvifDeviceInfo(host="10.0.0.5", manufacturer="Vendor", model="Cam-1")

    def get_stream_uri(self) -> str:
        return "rtsp://10.0.0.5:554/stream1"


def test_build_rtsp_url_defaults() -> None:
    assert build_rtsp_url("10.0.0.5") == "rtsp://10.0.0.5:554/stream1"


def test_build_rtsp_url_with_credentials() -> None:
    url = build_rtsp_url("10.0.0.5", username="admin", password="p@ss/word")
    assert url == "rtsp://admin:p%40ss%2Fword@10.0.0.5:554/stream1"


def test_build_rtsp_url_no_port() -> None:
    assert build_rtsp_url("10.0.0.5", port=None) == "rtsp://10.0.0.5/stream1"


def test_build_rtsp_url_custom_path() -> None:
    assert build_rtsp_url("10.0.0.5", path="/live/main") == "rtsp://10.0.0.5:554/live/main"


def test_fake_onvif_client_returns_device_info() -> None:
    client = FakeOnvifClient()
    info = client.get_device_information()
    assert info.host == "10.0.0.5"
    assert info.manufacturer == "Vendor"
    assert client.get_stream_uri().startswith("rtsp://")
