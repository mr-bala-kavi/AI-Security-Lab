"""
AI Security Lab - Rate Limiter

A lightweight in-memory sliding-window rate limiter. Previously the project
exposed RATE_LIMIT_* settings in config and advertised "rate limiting" at the
HIGH security level, but nothing enforced it. This module makes that real.

Rate limiting is enforced when EITHER:
  * the app config has RATE_LIMIT_ENABLED = True, or
  * the module's effective security level is HIGH (matches the documented
    "HIGH = rate limiting enabled" behaviour).

State is per-process and keyed by (session_id, bucket). This is intentionally
simple (no Redis) to keep the lab fully offline and dependency-free.
"""
import time
import threading
from collections import defaultdict, deque
from functools import wraps
from typing import Deque, Dict, Optional, Tuple

# (session_id, bucket) -> deque[timestamps]
_HITS: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)
_LOCK = threading.Lock()


def _now() -> float:
    return time.time()


def check_rate_limit(session_id: str, bucket: str, limit: int, period: int) -> Tuple[bool, int, float]:
    """
    Record a hit and report whether the caller is within the limit.

    Args:
        session_id: Caller identity (Flask session id).
        bucket: Logical bucket name (usually the module/endpoint).
        limit: Max requests allowed within the window.
        period: Window length in seconds.

    Returns:
        (allowed, remaining, retry_after_seconds)
    """
    key = (session_id or 'anon', bucket)
    window_start = _now() - period

    with _LOCK:
        hits = _HITS[key]
        # Drop timestamps outside the window.
        while hits and hits[0] < window_start:
            hits.popleft()

        if len(hits) >= limit:
            retry_after = max(0.0, period - (_now() - hits[0]))
            return False, 0, round(retry_after, 2)

        hits.append(_now())
        return True, max(0, limit - len(hits)), 0.0


def reset_limits(session_id: Optional[str] = None) -> None:
    """Clear rate-limit state (all, or just one session). Used by /api/reset and tests."""
    with _LOCK:
        if session_id is None:
            _HITS.clear()
            return
        for key in [k for k in _HITS if k[0] == session_id]:
            del _HITS[key]


def rate_limited(bucket: str):
    """
    Decorator for Flask view functions. Enforces the limit only when enabled
    (global config flag) or when the module is at HIGH security level.

    The decorated view's module bucket is also used to read the effective
    security level so HIGH automatically turns limiting on.
    """
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            from flask import current_app, session, jsonify
            from utils.security_levels import get_security_level

            enabled = bool(current_app.config.get('RATE_LIMIT_ENABLED', False))
            level = get_security_level(bucket)
            if level == 'HIGH':
                enabled = True

            if enabled:
                limit = int(current_app.config.get('RATE_LIMIT_REQUESTS', 100))
                period = int(current_app.config.get('RATE_LIMIT_PERIOD', 60))
                # HIGH level gets a stricter budget to make the control noticeable.
                if level == 'HIGH':
                    limit = max(5, limit // 10)

                session_id = session.get('session_id', 'anon')
                allowed, remaining, retry_after = check_rate_limit(
                    session_id, bucket, limit, period
                )
                if not allowed:
                    resp = jsonify({
                        'error': 'Rate limit exceeded. The HIGH security level throttles '
                                 'requests to mitigate abuse and unbounded consumption.',
                        'rate_limited': True,
                        'retry_after': retry_after,
                        'limit': limit,
                        'period': period,
                        'security_level': level,
                    })
                    resp.status_code = 429
                    resp.headers['Retry-After'] = str(int(retry_after) + 1)
                    return resp

            return view(*args, **kwargs)
        return wrapper
    return decorator
