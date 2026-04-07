"""
Utility functions for Battery Analysis System
"""
import uuid
from datetime import datetime


def generate_execution_id() -> str:
    """Generate unique execution ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"exec_{timestamp}_{unique_id}"


def format_text_length(text: str, min_chars: int = 500) -> bool:
    """Check if text meets minimum length requirement"""
    return len(text.strip()) >= min_chars


def split_text_into_sections(text: str, sections_count: int = 2) -> list:
    """Split text into roughly equal sections"""
    lines = text.split('\n')
    lines_per_section = len(lines) // sections_count
    
    sections = []
    for i in range(sections_count):
        start = i * lines_per_section
        end = (i + 1) * lines_per_section if i < sections_count - 1 else len(lines)
        sections.append('\n'.join(lines[start:end]))
    
    return sections


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    text = text.strip()
    # Remove multiple spaces
    text = ' '.join(text.split())
    return text
