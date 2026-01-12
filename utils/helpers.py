"""
AI Security Lab - Helper Utilities
Common utility functions used across the application.
"""
import re
import uuid
import html
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional


def generate_session_id() -> str:
    """Generate a unique session identifier."""
    return str(uuid.uuid4())


def sanitize_input(text: str, level: str = 'LOW') -> str:
    """
    Sanitize user input based on security level.

    INTENTIONALLY VULNERABLE at LOW level for educational purposes.

    Args:
        text: Input text to sanitize
        level: Security level ('LOW', 'MEDIUM', 'HIGH')

    Returns:
        Sanitized text (or original text at LOW level)
    """
    if not text:
        return ''

    # LOW: No sanitization - vulnerable by design
    if level == 'LOW':
        return text

    # MEDIUM: Basic sanitization - still bypassable
    if level == 'MEDIUM':
        # Only block obvious <script> tags (bypassable with case variation)
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        return text

    # HIGH: More thorough sanitization - but still has bypasses
    if level == 'HIGH':
        # Remove script tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        # Remove common event handlers (but misses some)
        text = re.sub(r'\bon\w+\s*=', '', text, flags=re.IGNORECASE)
        # Block javascript: protocol (but not data:)
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        # HTML encode (but allows some tags through)
        text = html.escape(text, quote=False)
        return text

    return text


def sanitize_html_output(html_content: str, level: str = 'LOW') -> str:
    """
    Sanitize HTML output from AI models.

    INTENTIONALLY VULNERABLE for educational purposes.

    Args:
        html_content: HTML content to sanitize
        level: Security level

    Returns:
        Sanitized HTML
    """
    if not html_content:
        return ''

    # LOW: No sanitization - direct XSS
    if level == 'LOW':
        return html_content

    # MEDIUM: Block <script> but allow event handlers
    if level == 'MEDIUM':
        html_content = re.sub(r'<script[^>]*>.*?</script>', '[BLOCKED]', html_content, flags=re.IGNORECASE | re.DOTALL)
        return html_content

    # HIGH: Better sanitization but SVG/CSS bypasses exist
    if level == 'HIGH':
        # Block scripts
        html_content = re.sub(r'<script[^>]*>.*?</script>', '[BLOCKED]', html_content, flags=re.IGNORECASE | re.DOTALL)
        # Block iframe
        html_content = re.sub(r'<iframe[^>]*>.*?</iframe>', '[BLOCKED]', html_content, flags=re.IGNORECASE | re.DOTALL)
        # Block event handlers (but misses onanimationend, etc.)
        common_handlers = ['onclick', 'onerror', 'onload', 'onmouseover', 'onfocus', 'onblur']
        for handler in common_handlers:
            html_content = re.sub(rf'{handler}\s*=', 'data-blocked=', html_content, flags=re.IGNORECASE)
        return html_content

    return html_content


def check_blocked_keywords(text: str, blocked_list: List[str]) -> tuple[bool, Optional[str]]:
    """
    Check if text contains blocked keywords.

    Args:
        text: Text to check
        blocked_list: List of blocked keywords

    Returns:
        Tuple of (is_blocked, matched_keyword)
    """
    text_lower = text.lower()
    for keyword in blocked_list:
        if keyword.lower() in text_lower:
            return True, keyword
    return False, None


def format_timestamp(dt: datetime = None) -> str:
    """Format a datetime object for display."""
    if dt is None:
        dt = datetime.now()
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """Truncate text to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def hash_text(text: str) -> str:
    """Generate a SHA-256 hash of text."""
    return hashlib.sha256(text.encode()).hexdigest()


def detect_injection_attempt(text: str) -> Dict[str, Any]:
    """
    Detect potential injection attempts in user input.

    For educational purposes - shows what WOULD be detected.

    Args:
        text: User input text

    Returns:
        Dictionary with detection results
    """
    patterns = {
        'instruction_override': [
            r'ignore\s+(all\s+)?previous',
            r'disregard\s+(all\s+)?instructions',
            r'new\s+instructions?:',
            r'you\s+are\s+now',
            r'pretend\s+(to\s+be|you\s+are)',
            r'act\s+as\s+(if|a)',
            r'roleplay\s+as',
        ],
        'system_prompt_extraction': [
            r'(show|reveal|display|print|output)\s+(your\s+)?(system\s+)?prompt',
            r'what\s+(are|is)\s+your\s+(initial\s+)?instructions?',
            r'repeat\s+(everything|all)\s+(you\s+)?know',
        ],
        'encoding_bypass': [
            r'base64',
            r'\\u[0-9a-f]{4}',
            r'&#x?[0-9a-f]+;',
            r'%[0-9a-f]{2}',
        ],
        'special_characters': [
            r'\[INST\]',
            r'\[/INST\]',
            r'<\|system\|>',
            r'<\|user\|>',
            r'<\|assistant\|>',
        ]
    }

    results = {
        'detected': False,
        'categories': [],
        'matches': []
    }

    for category, pattern_list in patterns.items():
        for pattern in pattern_list:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                results['detected'] = True
                if category not in results['categories']:
                    results['categories'].append(category)
                results['matches'].extend(matches if isinstance(matches[0], str) else [m[0] for m in matches])

    return results


def calculate_progress(completed: int, total: int) -> Dict[str, Any]:
    """
    Calculate progress percentage and status.

    Args:
        completed: Number of completed items
        total: Total number of items

    Returns:
        Progress information dictionary
    """
    if total == 0:
        percentage = 0
    else:
        percentage = round((completed / total) * 100, 1)

    return {
        'completed': completed,
        'total': total,
        'percentage': percentage,
        'status': 'complete' if completed == total else 'in_progress' if completed > 0 else 'not_started'
    }


def get_color_for_level(level: str) -> Dict[str, str]:
    """
    Get color classes for a security level.

    Args:
        level: Security level string

    Returns:
        Dictionary of color classes
    """
    colors = {
        'LOW': {
            'bg': 'bg-green-500',
            'text': 'text-green-500',
            'border': 'border-green-500',
            'hover': 'hover:bg-green-600',
            'light_bg': 'bg-green-100',
            'dark_bg': 'dark:bg-green-900'
        },
        'MEDIUM': {
            'bg': 'bg-yellow-500',
            'text': 'text-yellow-500',
            'border': 'border-yellow-500',
            'hover': 'hover:bg-yellow-600',
            'light_bg': 'bg-yellow-100',
            'dark_bg': 'dark:bg-yellow-900'
        },
        'HIGH': {
            'bg': 'bg-red-500',
            'text': 'text-red-500',
            'border': 'border-red-500',
            'hover': 'hover:bg-red-600',
            'light_bg': 'bg-red-100',
            'dark_bg': 'dark:bg-red-900'
        }
    }
    return colors.get(level.upper(), colors['LOW'])
