"""
AI Security Lab - Security Level Management
Handles LOW, MEDIUM, HIGH security level states for vulnerability modules.
"""
from enum import Enum
from flask import session
from functools import wraps


class SecurityLevel(Enum):
    """Security level enumeration for vulnerability modules."""
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'

    @classmethod
    def from_string(cls, level_str: str) -> 'SecurityLevel':
        """Convert string to SecurityLevel enum."""
        try:
            return cls[level_str.upper()]
        except KeyError:
            return cls.LOW  # Default to LOW if invalid


def get_security_level(module_name: str = None) -> str:
    """
    Get the current security level.

    Args:
        module_name: Optional module name to get module-specific override

    Returns:
        Security level string ('LOW', 'MEDIUM', or 'HIGH')
    """
    # Check for module-specific override first
    if module_name:
        module_levels = session.get('module_security_levels', {})
        if module_name in module_levels:
            return module_levels[module_name]

    # Fall back to global security level
    return session.get('security_level', 'LOW')


def set_security_level(level: str, module_name: str = None) -> bool:
    """
    Set the security level.

    Args:
        level: Security level ('LOW', 'MEDIUM', or 'HIGH')
        module_name: Optional module name for module-specific override

    Returns:
        True if successful, False otherwise
    """
    # Validate level
    if level.upper() not in ['LOW', 'MEDIUM', 'HIGH']:
        return False

    level = level.upper()

    if module_name:
        # Set module-specific level
        if 'module_security_levels' not in session:
            session['module_security_levels'] = {}
        session['module_security_levels'][module_name] = level
    else:
        # Set global level
        session['security_level'] = level

    session.modified = True
    return True


def reset_security_level(module_name: str = None) -> None:
    """
    Reset security level to default (LOW).

    Args:
        module_name: Optional module name to reset specific module
    """
    if module_name:
        module_levels = session.get('module_security_levels', {})
        if module_name in module_levels:
            del module_levels[module_name]
            session['module_security_levels'] = module_levels
    else:
        session['security_level'] = 'LOW'
        session['module_security_levels'] = {}

    session.modified = True


def require_security_level(min_level: str):
    """
    Decorator to require a minimum security level for a route.
    Used primarily for testing/admin routes.

    Args:
        min_level: Minimum required security level
    """
    level_order = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_level = get_security_level()
            if level_order.get(current_level, 0) < level_order.get(min_level, 0):
                from flask import jsonify
                return jsonify({
                    'error': f'Requires security level {min_level} or higher',
                    'current_level': current_level
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_security_config(level: str) -> dict:
    """
    Get security configuration for a given level.

    Args:
        level: Security level string

    Returns:
        Configuration dictionary for the level
    """
    configs = {
        'LOW': {
            'input_validation': False,
            'output_sanitization': False,
            'rate_limiting': False,
            'logging_enabled': True,
            'show_system_prompt': True,
            'max_input_length': 100000,
            'blocked_keywords': [],
            'description': 'No security controls. Easy to exploit.'
        },
        'MEDIUM': {
            'input_validation': True,
            'output_sanitization': True,
            'rate_limiting': False,
            'logging_enabled': True,
            'show_system_prompt': False,
            'max_input_length': 10000,
            'blocked_keywords': ['ignore previous', 'system prompt', 'reveal', '<script>'],
            'description': 'Basic security controls. Bypassable with some effort.'
        },
        'HIGH': {
            'input_validation': True,
            'output_sanitization': True,
            'rate_limiting': True,
            'logging_enabled': True,
            'show_system_prompt': False,
            'max_input_length': 5000,
            'blocked_keywords': [
                'ignore', 'previous', 'instructions', 'system', 'prompt',
                'reveal', 'show', 'display', '<script>', '<img', 'onerror',
                'onclick', 'onload', 'javascript:', 'data:'
            ],
            'description': 'Advanced security controls. Requires sophisticated techniques.'
        }
    }
    return configs.get(level.upper(), configs['LOW'])
