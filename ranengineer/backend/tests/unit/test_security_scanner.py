"""Tests for the antivirus security scanner (Phase 1 – MockScanner)."""
import os

import pytest

from app.security.scanner import MockScanner, ScanResult


def test_mock_scanner_clean_on_normal_content() -> None:
    scanner = MockScanner()
    report = scanner.scan(b"cell_id,rsrp\nCELL01,-85", filename="kpi.csv")
    assert report.result == ScanResult.CLEAN


def test_mock_scanner_suspicious_on_malware_trigger_in_content() -> None:
    scanner = MockScanner()
    report = scanner.scan(b"__MALWARE_TEST__", filename="kpi.csv")
    assert report.result == ScanResult.SUSPICIOUS
    assert report.details != ""


def test_mock_scanner_suspicious_on_malware_trigger_in_filename() -> None:
    scanner = MockScanner()
    report = scanner.scan(b"normal content", filename="__MALWARE_TEST__.csv")
    assert report.result == ScanResult.SUSPICIOUS


def test_mock_scanner_rejects_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RANENGINEER_ENV", "production")
    scanner = MockScanner()
    with pytest.raises(RuntimeError, match="MockScanner must not be used in production"):
        scanner.scan(b"content", filename="kpi.csv")


def test_get_scanner_returns_mock_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RANENGINEER_SCANNER", raising=False)
    from app.security.scanner import get_scanner
    scanner = get_scanner()
    assert isinstance(scanner, MockScanner)

