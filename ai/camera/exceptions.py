"""Exceptions for the camera subsystem."""


class CameraError(Exception):
    """Base exception for the camera subsystem."""


class CameraConfigError(CameraError):
    """Raised when camera configuration is invalid or cannot be loaded/saved."""
