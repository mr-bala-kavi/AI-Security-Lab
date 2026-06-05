"""Tests for the in-memory sliding-window rate limiter."""
from utils.rate_limiter import check_rate_limit, reset_limits


def setup_function():
    reset_limits()


def test_allows_under_limit():
    for _ in range(3):
        allowed, remaining, retry = check_rate_limit('s1', 'b', limit=5, period=60)
        assert allowed is True
    assert remaining == 2


def test_blocks_over_limit():
    for _ in range(5):
        check_rate_limit('s2', 'b', limit=5, period=60)
    allowed, remaining, retry = check_rate_limit('s2', 'b', limit=5, period=60)
    assert allowed is False
    assert remaining == 0
    assert retry >= 0


def test_buckets_are_isolated():
    for _ in range(5):
        check_rate_limit('s3', 'bucketA', limit=5, period=60)
    allowed, _, _ = check_rate_limit('s3', 'bucketB', limit=5, period=60)
    assert allowed is True


def test_sessions_are_isolated():
    for _ in range(5):
        check_rate_limit('userA', 'b', limit=5, period=60)
    allowed, _, _ = check_rate_limit('userB', 'b', limit=5, period=60)
    assert allowed is True


def test_reset_clears_session():
    for _ in range(5):
        check_rate_limit('userC', 'b', limit=5, period=60)
    reset_limits('userC')
    allowed, _, _ = check_rate_limit('userC', 'b', limit=5, period=60)
    assert allowed is True


def test_high_level_endpoint_is_throttled(client):
    """At HIGH security the rate limiter must eventually return 429."""
    client.post('/api/security-level', json={'level': 'HIGH'})
    statuses = []
    for _ in range(40):
        r = client.post('/modules/prompt-injection/chat', json={'message': 'hi'})
        statuses.append(r.status_code)
    assert 429 in statuses
