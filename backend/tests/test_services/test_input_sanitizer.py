"""
Tests for input_sanitizer utility
backend/app/utils/input_sanitizer.py

Covers: HTML tag stripping, javascript: protocol removal,
event handler removal, normal text preservation, edge cases.
"""
import pytest
from app.utils.input_sanitizer import sanitize_text


class TestSanitizeText:

    def test_strips_html_tags(self):
        """HTML tags are removed from input."""
        assert sanitize_text("<b>Bold</b> text") == "Bold text"
        assert sanitize_text("<script>alert(1)</script>") == "alert(1)"
        assert sanitize_text('<div class="x">content</div>') == "content"

    def test_strips_nested_tags(self):
        """Nested HTML tags are removed."""
        assert sanitize_text("<div><p><span>Hello</span></p></div>") == "Hello"

    def test_removes_javascript_protocol(self):
        """javascript: protocol strings are removed."""
        assert "javascript:" not in sanitize_text("javascript:alert(1)")
        assert "javascript:" not in sanitize_text("JAVASCRIPT:alert(1)")
        assert "javascript:" not in sanitize_text("Javascript:void(0)")

    def test_removes_event_handlers(self):
        """Event handler attributes like onclick= are removed."""
        result = sanitize_text('onclick=alert(1)')
        assert "onclick=" not in result.lower()

        result = sanitize_text('onmouseover=steal()')
        assert "onmouseover=" not in result.lower()

        result = sanitize_text('ONERROR=hack()')
        assert "onerror=" not in result.lower()

    def test_preserves_normal_text(self):
        """Normal text without HTML is preserved."""
        assert sanitize_text("Hello, World!") == "Hello, World!"
        assert sanitize_text("Binary Search Trees 101") == "Binary Search Trees 101"
        assert sanitize_text("Grade: A+ (95%)") == "Grade: A+ (95%)"

    def test_preserves_urls(self):
        """URLs in text are preserved."""
        url = "https://example.com/path?q=test"
        assert sanitize_text(url) == url

    def test_none_input(self):
        """None input returns None."""
        assert sanitize_text(None) is None

    def test_empty_string(self):
        """Empty string returns empty string."""
        assert sanitize_text("") == ""

    def test_whitespace_only(self):
        """Whitespace-only input is stripped to empty."""
        assert sanitize_text("   ") == ""

    def test_mixed_attack_vectors(self):
        """Combined attack patterns are all neutralized."""
        result = sanitize_text('<img src=x onerror=alert(1)>Click <a href="javascript:void(0)">here</a>')
        assert "<img" not in result
        assert "<a" not in result
        assert "javascript:" not in result
        assert "onerror=" not in result.lower()
        assert "Click" in result
        assert "here" in result

    def test_strips_and_trims(self):
        """Output is stripped of leading/trailing whitespace."""
        assert sanitize_text("  hello  ") == "hello"
        assert sanitize_text(" <b>  text  </b> ") == "text"

    def test_multiline_input(self):
        """Multiline input is handled correctly."""
        result = sanitize_text("Line 1\nLine 2\n<script>bad</script>")
        assert "Line 1\nLine 2\nbad" == result

    def test_self_closing_tags(self):
        """Self-closing HTML tags are removed."""
        assert sanitize_text("Hello<br/>World") == "HelloWorld"
        assert sanitize_text("Test<hr/>End") == "TestEnd"
