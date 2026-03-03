"""
Tests for app.services.document_converter

Covers:
- get_converted_pdf_path with various file types and paths
- has_converted_pdf with mocked os.path.exists
- convert_pptx_to_pdf: success, failure, timeout, file-not-found, PDF already exists
"""
import os

os.environ["DISABLE_ML_MODELS"] = "true"
os.environ["TESTING"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.services.document_converter import (
    convert_pptx_to_pdf,
    get_converted_pdf_path,
    has_converted_pdf,
)


# ---------------------------------------------------------------------------
# get_converted_pdf_path
# ---------------------------------------------------------------------------

class TestGetConvertedPdfPath:

    def test_pptx_extension(self):
        result = get_converted_pdf_path("/documents/lecture.pptx")
        assert result == "/documents/lecture.pdf"

    def test_ppt_extension(self):
        result = get_converted_pdf_path("/documents/old_slides.ppt")
        assert result == "/documents/old_slides.pdf"

    def test_path_with_spaces(self):
        result = get_converted_pdf_path("/my documents/my file.pptx")
        assert result == "/my documents/my file.pdf"

    def test_nested_path(self):
        result = get_converted_pdf_path("/a/b/c/d/presentation.pptx")
        assert result == "/a/b/c/d/presentation.pdf"

    def test_preserves_stem_with_dots(self):
        result = get_converted_pdf_path("/docs/v2.1.final.pptx")
        assert result == "/docs/v2.1.final.pdf"


# ---------------------------------------------------------------------------
# has_converted_pdf
# ---------------------------------------------------------------------------

class TestHasConvertedPdf:

    def test_returns_true_when_pdf_exists(self):
        with patch("app.services.document_converter.os.path.exists", return_value=True):
            assert has_converted_pdf("/docs/lecture.pptx") is True

    def test_returns_false_when_pdf_missing(self):
        with patch("app.services.document_converter.os.path.exists", return_value=False):
            assert has_converted_pdf("/docs/lecture.pptx") is False


# ---------------------------------------------------------------------------
# convert_pptx_to_pdf
# ---------------------------------------------------------------------------

class TestConvertPptxToPdf:

    def test_file_not_found_raises(self, tmp_path):
        """Non-existent input file should raise FileNotFoundError."""
        fake_path = str(tmp_path / "nonexistent.pptx")
        try:
            convert_pptx_to_pdf(fake_path)
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError as e:
            assert "not found" in str(e).lower()

    def test_returns_existing_pdf_without_converting(self, tmp_path):
        """If the PDF already exists, skip conversion and return path."""
        pptx_file = tmp_path / "slides.pptx"
        pptx_file.write_text("fake pptx content")

        # Pre-create the PDF so the function finds it
        pdf_file = tmp_path / "slides.pdf"
        pdf_file.write_text("fake pdf content")

        result = convert_pptx_to_pdf(str(pptx_file))
        assert result == str(pdf_file)

    def test_successful_conversion(self, tmp_path):
        """Mock subprocess.run to simulate successful LibreOffice conversion."""
        pptx_file = tmp_path / "lecture.pptx"
        pptx_file.write_text("fake pptx")

        expected_pdf = tmp_path / "lecture.pdf"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        with patch("app.services.document_converter.subprocess.run", return_value=mock_result) as mock_run:
            # After subprocess.run, the function checks if the pdf exists.
            # We need the file to actually exist at that point.
            # Use a side_effect to create the file when subprocess.run is called.
            def create_pdf(*args, **kwargs):
                expected_pdf.write_text("converted pdf")
                return mock_result

            mock_run.side_effect = create_pdf

            result = convert_pptx_to_pdf(str(pptx_file))
            assert result == str(expected_pdf)
            mock_run.assert_called_once()

    def test_conversion_failure_raises(self, tmp_path):
        """Non-zero return code from LibreOffice should raise an Exception."""
        pptx_file = tmp_path / "bad.pptx"
        pptx_file.write_text("fake pptx")

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "LibreOffice error"

        with patch("app.services.document_converter.subprocess.run", return_value=mock_result):
            try:
                convert_pptx_to_pdf(str(pptx_file))
                assert False, "Expected Exception for failed conversion"
            except Exception as e:
                assert "Conversion failed" in str(e) or "LibreOffice error" in str(e)

    def test_conversion_timeout_raises(self, tmp_path):
        """subprocess.TimeoutExpired should be caught and re-raised as Exception."""
        pptx_file = tmp_path / "huge.pptx"
        pptx_file.write_text("fake pptx")

        with patch(
            "app.services.document_converter.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="soffice", timeout=60),
        ):
            try:
                convert_pptx_to_pdf(str(pptx_file))
                assert False, "Expected Exception for timeout"
            except Exception as e:
                assert "timed out" in str(e).lower()

    def test_custom_output_dir(self, tmp_path):
        """Conversion with a custom output directory."""
        pptx_file = tmp_path / "slides.pptx"
        pptx_file.write_text("fake pptx")

        output_dir = tmp_path / "output"

        expected_pdf = output_dir / "slides.pdf"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        def create_pdf(*args, **kwargs):
            output_dir.mkdir(parents=True, exist_ok=True)
            expected_pdf.write_text("converted pdf")
            return mock_result

        with patch("app.services.document_converter.subprocess.run", side_effect=create_pdf):
            result = convert_pptx_to_pdf(str(pptx_file), output_dir=str(output_dir))
            assert result == str(expected_pdf)
