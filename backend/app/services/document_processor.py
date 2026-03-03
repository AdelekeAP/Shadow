"""
Document Processor Service - Phase 2 Week 2
Extracts text from PDF and PowerPoint files for study plan generation
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from PyPDF2 import PdfReader
from pptx import Presentation
from openai import OpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract all text content from a PDF file

    Args:
        file_path: Path to PDF file

    Returns:
        Extracted text as string

    Raises:
        Exception: If PDF reading fails
    """
    try:
        logger.info(f"📄 Extracting text from PDF: {file_path}")

        reader = PdfReader(file_path)
        text = ""

        # Extract text from each page
        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Page {page_num} ---\n{page_text}"

        if not text.strip():
            logger.warning("⚠️ No text extracted from PDF (might be image-based)")
            return "No text content found. PDF might contain only images."

        logger.info(f"✅ Extracted {len(text)} characters from {len(reader.pages)} pages")
        return text.strip()

    except Exception as e:
        logger.error(f"❌ Error extracting PDF text: {e}")
        raise Exception(f"Failed to read PDF file: {str(e)}")


def extract_text_from_pptx(file_path: str) -> str:
    """
    Extract all text content from a PowerPoint file

    Args:
        file_path: Path to PPTX file

    Returns:
        Extracted text as string

    Raises:
        Exception: If PowerPoint reading fails
    """
    try:
        logger.info(f"📊 Extracting text from PPTX: {file_path}")

        prs = Presentation(file_path)
        text = ""

        # Extract text from each slide
        for slide_num, slide in enumerate(prs.slides, 1):
            slide_text = f"\n--- Slide {slide_num} ---\n"

            # Extract text from all shapes in the slide
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text:
                    slide_text += shape.text + "\n"

            if slide_text.strip():
                text += slide_text

        if not text.strip():
            logger.warning("⚠️ No text extracted from PowerPoint")
            return "No text content found in slides."

        logger.info(f"✅ Extracted {len(text)} characters from {len(prs.slides)} slides")
        return text.strip()

    except Exception as e:
        logger.error(f"❌ Error extracting PPTX text: {e}")
        raise Exception(f"Failed to read PowerPoint file: {str(e)}")


def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from either PDF or PPTX file based on extension

    Args:
        file_path: Path to file

    Returns:
        Extracted text

    Raises:
        ValueError: If file type not supported
        Exception: If extraction fails
    """
    file_ext = file_path.lower().split('.')[-1]

    if file_ext == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_ext in ['pptx', 'ppt']:
        return extract_text_from_pptx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_ext}. Only PDF and PPTX are supported.")


def extract_topics_with_gpt4(slide_text: str, max_length: int = 3000) -> Dict[str, Any]:
    """
    Use GPT-4 to intelligently extract topics from slide text

    Args:
        slide_text: Raw text extracted from slides
        max_length: Maximum characters to send to GPT-4

    Returns:
        Dict with main_topic, subtopics, key_concepts, difficulty

    Example:
        {
            "main_topic": "Binary Search Trees",
            "subtopics": ["Introduction", "Insertion", "Deletion", "Traversal"],
            "key_concepts": ["BST property", "Recursive algorithms"],
            "difficulty": "intermediate"
        }
    """
    if not client:
        logger.warning("⚠️ OpenAI client not initialized, skipping topic extraction")
        return {
            "main_topic": "Unknown Topic",
            "subtopics": [],
            "key_concepts": [],
            "difficulty": "intermediate"
        }

    try:
        # Truncate text if too long (keep first portion)
        truncated_text = slide_text[:max_length] if len(slide_text) > max_length else slide_text

        logger.info(f"🤖 Extracting topics with GPT-4 from {len(truncated_text)} characters...")

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at analyzing lecture slides and extracting key educational topics. Return responses in valid JSON format only."
                },
                {
                    "role": "user",
                    "content": f"""Analyze these lecture slides and extract:
1. Main topic (1-5 words)
2. 4-6 subtopics in logical learning order
3. Key concepts mentioned
4. Difficulty level (beginner/intermediate/advanced)

Slides content:
{truncated_text}

Return ONLY valid JSON in this exact format:
{{
  "main_topic": "...",
  "subtopics": ["...", "..."],
  "key_concepts": ["...", "..."],
  "difficulty": "..."
}}"""
                }
            ],
            temperature=0.3,
            max_tokens=500
        )

        result_text = response.choices[0].message.content.strip()

        # Parse JSON response
        try:
            topics = json.loads(result_text)
            logger.info(f"✅ Extracted main topic: {topics.get('main_topic')}")
            logger.info(f"   Subtopics: {', '.join(topics.get('subtopics', []))}")
            return topics

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse GPT-4 JSON response: {e}")
            logger.error(f"Response was: {result_text}")

            # Return fallback structure
            return {
                "main_topic": "Lecture Content",
                "subtopics": ["Topic 1", "Topic 2", "Topic 3"],
                "key_concepts": [],
                "difficulty": "intermediate"
            }

    except Exception as e:
        logger.error(f"❌ Error in GPT-4 topic extraction: {e}")
        return {
            "main_topic": "Lecture Content",
            "subtopics": [],
            "key_concepts": [],
            "difficulty": "intermediate"
        }


def validate_file(file_path: str, max_size_mb: int = 10) -> Dict[str, Any]:
    """
    Validate uploaded file before processing

    Args:
        file_path: Path to file
        max_size_mb: Maximum file size in MB

    Returns:
        Dict with is_valid, error_message, file_info
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return {
                "is_valid": False,
                "error_message": "File not found",
                "file_info": None
            }

        # Check file size
        file_size_bytes = os.path.getsize(file_path)
        file_size_mb = file_size_bytes / (1024 * 1024)

        if file_size_mb > max_size_mb:
            return {
                "is_valid": False,
                "error_message": f"File too large ({file_size_mb:.1f}MB). Maximum size is {max_size_mb}MB.",
                "file_info": None
            }

        # Check file extension
        file_ext = file_path.lower().split('.')[-1]
        if file_ext not in ['pdf', 'pptx', 'ppt']:
            return {
                "is_valid": False,
                "error_message": f"Unsupported file type: .{file_ext}. Only PDF and PPTX are supported.",
                "file_info": None
            }

        # All validations passed
        return {
            "is_valid": True,
            "error_message": None,
            "file_info": {
                "name": os.path.basename(file_path),
                "size_mb": round(file_size_mb, 2),
                "type": file_ext
            }
        }

    except Exception as e:
        logger.error(f"❌ Error validating file: {e}")
        return {
            "is_valid": False,
            "error_message": f"Error validating file: {str(e)}",
            "file_info": None
        }


def process_document_for_study_plan(
    file_path: str,
    topic_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Complete document processing pipeline for study plan generation

    Args:
        file_path: Path to uploaded document
        topic_hint: Optional topic provided by student (overrides extraction)

    Returns:
        Dict with:
        - extracted_text: Full text content
        - main_topic: Main topic (from GPT-4 or hint)
        - subtopics: List of subtopics
        - key_concepts: List of key concepts
        - difficulty: Estimated difficulty level
        - success: Boolean indicating success
        - error: Error message if failed
    """
    try:
        # Validate file
        validation = validate_file(file_path)
        if not validation["is_valid"]:
            return {
                "success": False,
                "error": validation["error_message"],
                "extracted_text": None
            }

        logger.info(f"📄 Processing document: {validation['file_info']['name']}")

        # Extract text
        extracted_text = extract_text_from_file(file_path)

        # Extract topics with GPT-4
        topics = extract_topics_with_gpt4(extracted_text)

        # Use topic hint if provided
        if topic_hint:
            topics["main_topic"] = topic_hint
            logger.info(f"✅ Using provided topic: {topic_hint}")

        return {
            "success": True,
            "error": None,
            "extracted_text": extracted_text,
            "main_topic": topics["main_topic"],
            "subtopics": topics["subtopics"],
            "key_concepts": topics["key_concepts"],
            "difficulty": topics["difficulty"],
            "file_info": validation["file_info"]
        }

    except Exception as e:
        logger.error(f"❌ Error processing document: {e}")
        return {
            "success": False,
            "error": f"Failed to process document: {str(e)}",
            "extracted_text": None
        }
