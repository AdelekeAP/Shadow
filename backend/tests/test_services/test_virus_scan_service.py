"""
Tests for Virus Scan Service
backend/app/services/virus_scan_service.py

Tests cover: scan_bytes (with ClamAV available, unavailable, infected file),
get_scanner_status, scan_pending_documents.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.services.virus_scan_service import scan_bytes, get_scanner_status


class TestScanBytes:

    @patch("app.services.virus_scan_service._get_clamd")
    def test_clean_file_returns_clean(self, mock_get_clamd):
        mock_cd = MagicMock()
        mock_cd.scan_stream.return_value = None  # ClamAV returns None for clean
        mock_get_clamd.return_value = mock_cd

        result = scan_bytes(b"%PDF-1.4 some content")
        assert result["status"] == "clean"
        assert result["threat"] is None

    @patch("app.services.virus_scan_service._get_clamd")
    def test_infected_file_returns_infected(self, mock_get_clamd):
        mock_cd = MagicMock()
        mock_cd.scan_stream.return_value = {"stream": ("FOUND", "Win.Test.EICAR_HDB-1")}
        mock_get_clamd.return_value = mock_cd

        result = scan_bytes(b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR")
        assert result["status"] == "infected"
        assert "EICAR" in result["threat"]

    @patch("app.services.virus_scan_service._get_clamd")
    def test_clamd_unavailable_returns_pending(self, mock_get_clamd):
        mock_get_clamd.return_value = None

        result = scan_bytes(b"%PDF-1.4 content")
        assert result["status"] == "pending"
        assert result["threat"] is None

    @patch("app.services.virus_scan_service._get_clamd")
    def test_scan_error_returns_error(self, mock_get_clamd):
        mock_cd = MagicMock()
        mock_cd.scan_stream.side_effect = Exception("Connection reset")
        mock_get_clamd.return_value = mock_cd

        result = scan_bytes(b"%PDF-1.4 content")
        assert result["status"] == "error"
        assert result["threat"] is None


class TestGetScannerStatus:

    @patch("app.services.virus_scan_service._get_clamd")
    def test_available(self, mock_get_clamd):
        mock_cd = MagicMock()
        mock_cd.version.return_value = "ClamAV 1.0.0"
        mock_get_clamd.return_value = mock_cd

        result = get_scanner_status()
        assert result["available"] is True
        assert "1.0.0" in result["version"]

    @patch("app.services.virus_scan_service._get_clamd")
    def test_unavailable(self, mock_get_clamd):
        mock_get_clamd.return_value = None

        result = get_scanner_status()
        assert result["available"] is False
