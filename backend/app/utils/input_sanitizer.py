"""
Central input sanitizer — prevents XSS in user-supplied text fields.
"""
import html
import re


def sanitize_text(text: str) -> str:
    """Strip HTML tags and dangerous patterns from user input to prevent XSS."""
    if not text:
        return text
    # Decode HTML entities first so encoded attacks are caught (e.g. &lt;script&gt;)
    cleaned = html.unescape(text)
    # Remove HTML tags (handles unclosed tags and multi-line)
    cleaned = re.sub(r'<[^>]*?>', '', cleaned, flags=re.DOTALL)
    # Remove any remaining unclosed tags (e.g. "<script" without closing ">")
    cleaned = re.sub(r'<[^>]*$', '', cleaned)
    # Remove javascript: protocol (with optional whitespace and encoding tricks)
    cleaned = re.sub(r'j\s*a\s*v\s*a\s*s\s*c\s*r\s*i\s*p\s*t\s*:', '', cleaned, flags=re.IGNORECASE)
    # Remove vbscript: protocol
    cleaned = re.sub(r'vbscript\s*:', '', cleaned, flags=re.IGNORECASE)
    # Remove data: URIs with dangerous MIME types
    cleaned = re.sub(r'data\s*:\s*text/html', '', cleaned, flags=re.IGNORECASE)
    # Remove event handlers (on* attributes)
    cleaned = re.sub(r'on\w+\s*=', '', cleaned, flags=re.IGNORECASE)
    # Escape any remaining angle brackets to prevent reconstruction
    cleaned = cleaned.replace('<', '&lt;').replace('>', '&gt;')
    return cleaned.strip()
