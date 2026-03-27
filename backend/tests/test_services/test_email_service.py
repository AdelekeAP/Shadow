"""
Tests for email_service
backend/app/services/email_service.py

Covers: SMTP configuration detection, send_email with mocked SMTP,
HTML template XSS-safe escaping, dev mode logging.
"""
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# SMTP configuration detection
# ---------------------------------------------------------------------------

class TestSmtpConfigured:

    def test_returns_false_when_env_vars_missing(self, monkeypatch):
        """_smtp_configured returns False when SMTP env vars are not set."""
        monkeypatch.delenv("SMTP_HOST", raising=False)
        monkeypatch.delenv("SMTP_USERNAME", raising=False)
        monkeypatch.delenv("SMTP_PASSWORD", raising=False)

        # Reload module to pick up env changes
        import importlib
        import app.services.email_service as mod
        importlib.reload(mod)

        assert mod._smtp_configured() is False

    def test_returns_true_when_all_set(self, monkeypatch):
        """_smtp_configured returns True when all SMTP vars are present."""
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "secret123")

        import importlib
        import app.services.email_service as mod
        importlib.reload(mod)

        assert mod._smtp_configured() is True

    def test_returns_false_with_partial_config(self, monkeypatch):
        """_smtp_configured returns False when only some vars are set."""
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.delenv("SMTP_USERNAME", raising=False)
        monkeypatch.setenv("SMTP_PASSWORD", "secret123")

        import importlib
        import app.services.email_service as mod
        importlib.reload(mod)

        assert mod._smtp_configured() is False


# ---------------------------------------------------------------------------
# _send_email
# ---------------------------------------------------------------------------

class TestSendEmail:

    def test_dev_mode_logs_instead_of_sending(self, monkeypatch, caplog):
        """When SMTP not configured, logs the email instead of sending."""
        monkeypatch.delenv("SMTP_HOST", raising=False)
        monkeypatch.delenv("SMTP_USERNAME", raising=False)
        monkeypatch.delenv("SMTP_PASSWORD", raising=False)

        import importlib
        import app.services.email_service as mod
        importlib.reload(mod)

        import logging
        with caplog.at_level(logging.INFO, logger="app.services.email_service"):
            result = mod._send_email("test@pau.edu.ng", "Test Subject", "<p>Test</p>")

        assert result is True
        assert "SMTP not configured" in caplog.text

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_with_smtp_success(self, mock_smtp_class, monkeypatch):
        """Successfully sends via SMTP when configured."""
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "587")
        monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "secret123")

        import importlib
        import app.services.email_service as mod
        importlib.reload(mod)

        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        result = mod._send_email("test@pau.edu.ng", "Test", "<p>Hello</p>")

        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user@example.com", "secret123")
        mock_server.sendmail.assert_called_once()

    @patch("app.services.email_service.smtplib.SMTP")
    def test_send_with_smtp_failure(self, mock_smtp_class, monkeypatch):
        """Returns True (fire-and-forget) even when SMTP would fail in background."""
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "587")
        monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "secret123")

        import importlib
        import app.services.email_service as mod
        importlib.reload(mod)

        mock_smtp_class.return_value.__enter__ = MagicMock(
            side_effect=Exception("Connection refused")
        )
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        # _send_email now always returns True immediately (async background send)
        result = mod._send_email("test@pau.edu.ng", "Test", "<p>Hello</p>")
        assert result is True


# ---------------------------------------------------------------------------
# XSS escaping in templates
# ---------------------------------------------------------------------------

class TestXSSEscaping:

    def test_build_email_escapes_subject(self):
        """Subject containing HTML entities is escaped."""
        from app.services.email_service import _build_email

        html = _build_email(
            subject='<script>alert("xss")</script>',
            heading="Test",
            body_html="<p>Safe body</p>",
            cta_text="Click",
            cta_url="https://example.com",
        )

        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_build_email_escapes_cta_url(self):
        """CTA URL with dangerous quotes is HTML-escaped."""
        from app.services.email_service import _build_email

        html = _build_email(
            subject="Test",
            heading="Test",
            body_html="<p>Body</p>",
            cta_text="Click",
            cta_url='https://example.com?x="injected"&y=<tag>',
        )

        # Quotes and angle brackets in the URL should be HTML-escaped
        assert '&quot;' in html or '&#x27;' in html or '&lt;' in html
        assert 'x="injected"' not in html
        assert "<tag>" not in html

    def test_build_email_escapes_cta_text(self):
        """CTA text with HTML is escaped."""
        from app.services.email_service import _build_email

        html = _build_email(
            subject="Test",
            heading="Test",
            body_html="<p>Body</p>",
            cta_text='<img src=x onerror=alert(1)>',
            cta_url="https://example.com",
        )

        assert "<img src=x" not in html
        assert "&lt;img" in html

    def test_detail_row_escapes_values(self):
        """_detail_row escapes label and value."""
        from app.services.email_service import _detail_row

        html = _detail_row('<b>Label</b>', '<script>alert(1)</script>')

        assert "<b>Label</b>" not in html
        assert "&lt;b&gt;Label&lt;/b&gt;" in html
        assert "<script>" not in html

    def test_send_verification_escapes_name(self, monkeypatch):
        """Verification email escapes user name to prevent XSS."""
        monkeypatch.delenv("SMTP_HOST", raising=False)
        monkeypatch.delenv("SMTP_USERNAME", raising=False)
        monkeypatch.delenv("SMTP_PASSWORD", raising=False)

        import importlib
        import app.services.email_service as mod
        importlib.reload(mod)

        # Patch _send_email to capture the HTML body
        captured = {}
        original_send = mod._send_email

        def capture_send(to, subject, html_body):
            captured["html"] = html_body
            return True

        with patch.object(mod, "_send_email", side_effect=capture_send):
            mod.send_verification_email(
                "test@pau.edu.ng",
                "test-token",
                '<script>alert("xss")</script>',
            )

        assert "<script>" not in captured.get("html", "")


# ---------------------------------------------------------------------------
# Public email functions (smoke tests)
# ---------------------------------------------------------------------------

class TestEmailFunctions:

    def test_send_verification_email(self, monkeypatch):
        """send_verification_email runs without error in dev mode."""
        monkeypatch.delenv("SMTP_HOST", raising=False)
        monkeypatch.delenv("SMTP_USERNAME", raising=False)
        monkeypatch.delenv("SMTP_PASSWORD", raising=False)

        import importlib
        import app.services.email_service as mod
        importlib.reload(mod)

        result = mod.send_verification_email("test@pau.edu.ng", "token123", "John")
        assert result is True

    def test_send_password_reset_email(self, monkeypatch):
        """send_password_reset_email runs without error in dev mode."""
        monkeypatch.delenv("SMTP_HOST", raising=False)
        monkeypatch.delenv("SMTP_USERNAME", raising=False)
        monkeypatch.delenv("SMTP_PASSWORD", raising=False)

        import importlib
        import app.services.email_service as mod
        importlib.reload(mod)

        result = mod.send_password_reset_email("test@pau.edu.ng", "token123", "John")
        assert result is True

    def test_send_task_overdue_email(self, monkeypatch):
        """send_task_overdue_email runs without error in dev mode."""
        monkeypatch.delenv("SMTP_HOST", raising=False)
        monkeypatch.delenv("SMTP_USERNAME", raising=False)
        monkeypatch.delenv("SMTP_PASSWORD", raising=False)

        import importlib
        import app.services.email_service as mod
        importlib.reload(mod)

        result = mod.send_task_overdue_email(
            "test@pau.edu.ng", "John", "Assignment 1", "CSC201", "2026-03-10"
        )
        assert result is True

    def test_send_cgpa_alert_email(self, monkeypatch):
        """send_cgpa_alert_email runs without error in dev mode."""
        monkeypatch.delenv("SMTP_HOST", raising=False)
        monkeypatch.delenv("SMTP_USERNAME", raising=False)
        monkeypatch.delenv("SMTP_PASSWORD", raising=False)

        import importlib
        import app.services.email_service as mod
        importlib.reload(mod)

        result = mod.send_cgpa_alert_email(
            "test@pau.edu.ng", "John", 3.8, 4.5, "Second Class Upper"
        )
        assert result is True

    def test_send_study_plan_complete_email(self, monkeypatch):
        """send_study_plan_complete_email runs without error in dev mode."""
        monkeypatch.delenv("SMTP_HOST", raising=False)
        monkeypatch.delenv("SMTP_USERNAME", raising=False)
        monkeypatch.delenv("SMTP_PASSWORD", raising=False)

        import importlib
        import app.services.email_service as mod
        importlib.reload(mod)

        result = mod.send_study_plan_complete_email(
            "test@pau.edu.ng", "John", "Binary Trees", 7, 7
        )
        assert result is True
