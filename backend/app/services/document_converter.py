"""
Document Converter Service
Converts PowerPoint files to PDF for in-browser viewing
"""
import subprocess
import os
import sys
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _find_libreoffice() -> str:
    """
    Locate the LibreOffice executable across platforms.

    Checks LIBREOFFICE_PATH env var first, then platform-specific defaults,
    then falls back to PATH lookup.

    Returns:
        Absolute path to the LibreOffice binary

    Raises:
        FileNotFoundError: If LibreOffice is not found
    """
    # 1. Check env var override
    env_path = os.getenv("LIBREOFFICE_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    # 2. Platform-specific default paths
    candidates = []
    if sys.platform == "darwin":
        candidates.append("/Applications/LibreOffice.app/Contents/MacOS/soffice")
    elif sys.platform == "win32":
        for pf in [os.environ.get("ProgramFiles", ""), os.environ.get("ProgramFiles(x86)", "")]:
            if pf:
                candidates.append(os.path.join(pf, "LibreOffice", "program", "soffice.exe"))
    else:  # Linux and other Unix
        candidates.append("/usr/bin/libreoffice")
        candidates.append("/usr/bin/soffice")

    for path in candidates:
        if os.path.isfile(path):
            return path

    # 3. Fall back to PATH lookup
    found = shutil.which("libreoffice") or shutil.which("soffice")
    if found:
        return found

    raise FileNotFoundError(
        "LibreOffice not found. Install it or set the LIBREOFFICE_PATH environment variable."
    )


def convert_pptx_to_pdf(input_path: str, output_dir: str = None) -> str:
    """
    Convert PowerPoint file to PDF using LibreOffice

    Args:
        input_path: Path to the PPTX/PPT file
        output_dir: Directory to save the converted PDF (defaults to same directory as input)

    Returns:
        Path to the converted PDF file

    Raises:
        Exception: If conversion fails
    """
    try:
        input_file = Path(input_path)

        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Determine output directory
        if output_dir is None:
            output_dir = input_file.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        # Expected output PDF path
        output_pdf = output_dir / f"{input_file.stem}.pdf"

        # Check if a valid PDF already exists (non-empty)
        if output_pdf.exists() and output_pdf.stat().st_size > 0:
            logger.info(f"✅ PDF already exists: {output_pdf}")
            return str(output_pdf)

        logger.info(f"🔄 Converting {input_file.name} to PDF...")

        # Locate LibreOffice binary (cross-platform)
        libreoffice_bin = _find_libreoffice()
        logger.info(f"Using LibreOffice at: {libreoffice_bin}")

        # LibreOffice command for conversion
        # --headless: Run without GUI
        # --convert-to pdf: Convert to PDF format
        # --outdir: Output directory
        libreoffice_cmd = [
            libreoffice_bin,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(output_dir),
            str(input_path)
        ]

        # Run conversion
        result = subprocess.run(
            libreoffice_cmd,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )

        if result.returncode != 0:
            logger.error(f"❌ LibreOffice conversion failed: {result.stderr}")
            raise Exception(f"Conversion failed: {result.stderr}")

        # Verify the PDF was created
        if not output_pdf.exists():
            raise Exception(f"Conversion completed but PDF not found at {output_pdf}")

        logger.info(f"✅ Successfully converted to PDF: {output_pdf}")
        return str(output_pdf)

    except subprocess.TimeoutExpired:
        logger.error("❌ Conversion timed out")
        raise Exception("Document conversion timed out (file may be too large)")
    except Exception as e:
        logger.error(f"❌ Error converting document: {e}")
        raise


def get_converted_pdf_path(original_path: str) -> str:
    """
    Get the path where the converted PDF would be stored

    Args:
        original_path: Path to the original PPTX/PPT file

    Returns:
        Path where the PDF would be stored
    """
    original_file = Path(original_path)
    return str(original_file.parent / f"{original_file.stem}.pdf")


def has_converted_pdf(original_path: str) -> bool:
    """
    Check if a converted PDF already exists for the given file

    Args:
        original_path: Path to the original PPTX/PPT file

    Returns:
        True if converted PDF exists, False otherwise
    """
    pdf_path = get_converted_pdf_path(original_path)
    return os.path.exists(pdf_path)
