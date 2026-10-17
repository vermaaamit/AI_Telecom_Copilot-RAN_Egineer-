"""Antivirus / security scanner abstraction.

Phase 1 provides:
  - AntivirusScanner  – abstract interface
  - ClamAVScanner     – real implementation (ClamAV daemon via clamd socket)
  - MockScanner       – development/test stub (safe by default)

Production MUST use ClamAVScanner.
Development/CI may use MockScanner when ClamAV is unavailable.

Never silently skip security scanning in production.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class ScanResult(str, Enum):
    CLEAN = "CLEAN"
    SUSPICIOUS = "SUSPICIOUS"
    ERROR = "ERROR"


@dataclass
class ScanReport:
    result: ScanResult
    details: str = ""


class AntivirusScanner(ABC):
    """Abstract antivirus scanner interface."""

    @abstractmethod
    def scan(self, content: bytes, filename: str = "") -> ScanReport:
        """Scan file content and return a ScanReport."""


class MockScanner(AntivirusScanner):
    """Development/test scanner stub.

    - Always returns CLEAN unless the filename or content contains
      the magic string '__MALWARE_TEST__' (used in tests).
    - Must NOT be used in production (RANENGINEER_ENV != development).
    """

    _TRIGGER = b"__MALWARE_TEST__"

    def scan(self, content: bytes, filename: str = "") -> ScanReport:
        env = os.getenv("RANENGINEER_ENV", "development").lower()
        if env == "production":
            raise RuntimeError(
                "MockScanner must not be used in production. "
                "Set RANENGINEER_ENV=development or deploy ClamAV."
            )
        if self._TRIGGER in content or self._TRIGGER.decode() in filename:
            return ScanReport(result=ScanResult.SUSPICIOUS, details="Test malware trigger detected")
        return ScanReport(result=ScanResult.CLEAN)


class ClamAVScanner(AntivirusScanner):
    """ClamAV-based scanner using the clamd daemon.

    Requires:
      CLAMAV_HOST  (default: clamav)
      CLAMAV_PORT  (default: 3310)

    If the daemon is unreachable, raises RuntimeError so the caller
    can block the upload rather than silently proceeding.
    """

    def __init__(self, host: str | None = None, port: int | None = None) -> None:
        self.host = host or os.getenv("CLAMAV_HOST", "clamav")
        self.port = port or int(os.getenv("CLAMAV_PORT", "3310"))

    def scan(self, content: bytes, filename: str = "") -> ScanReport:
        try:
            import socket

            with socket.create_connection((self.host, self.port), timeout=10) as sock:
                # Use INSTREAM protocol
                sock.sendall(b"zINSTREAM\0")
                chunk_size = len(content)
                sock.sendall(chunk_size.to_bytes(4, "big"))
                sock.sendall(content)
                sock.sendall((0).to_bytes(4, "big"))
                response = b""
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                    if b"\0" in chunk:
                        break
            decoded = response.rstrip(b"\0").decode(errors="replace")
            if "FOUND" in decoded:
                return ScanReport(result=ScanResult.SUSPICIOUS, details=decoded)
            if "ERROR" in decoded:
                return ScanReport(result=ScanResult.ERROR, details=decoded)
            return ScanReport(result=ScanResult.CLEAN)
        except OSError as exc:
            raise RuntimeError(
                f"ClamAV daemon unreachable at {self.host}:{self.port}. "
                "Ensure the clamav Docker service is running."
            ) from exc


def get_scanner() -> AntivirusScanner:
    """Return the appropriate scanner based on environment configuration.

    RANENGINEER_SCANNER=clamav   → ClamAVScanner
    RANENGINEER_SCANNER=mock     → MockScanner  (development only)
    Default                      → MockScanner  (development only)
    """
    scanner_type = os.getenv("RANENGINEER_SCANNER", "mock").lower()
    if scanner_type == "clamav":
        return ClamAVScanner()
    return MockScanner()


__all__ = ["AntivirusScanner", "ClamAVScanner", "MockScanner", "ScanReport", "ScanResult", "get_scanner"]

