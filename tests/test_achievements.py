"""Tests for the achievements/gamification engine."""
from utils.achievements import compute_achievements


def _ids(entries):
    return {e['id'] for e in entries}


def test_no_progress_unlocks_nothing():
    result = compute_achievements({'completed': 0, 'total': 10})
    assert result['unlocked_count'] == 0
    assert result['rank'] == 'Novice'
    assert result['points'] == 0


def test_first_blood_unlocks():
    result = compute_achievements({'completed': 1, 'total': 10})
    assert 'first_blood' in _ids(result['unlocked'])


def test_grandmaster_full_clear():
    result = compute_achievements({'completed': 10, 'total': 10})
    ids = _ids(result['unlocked'])
    assert 'grandmaster' in ids
    assert 'half_way' in ids
    assert result['rank'] in ('Adept', 'Expert', 'Grandmaster')


def test_module_specific_badges():
    result = compute_achievements({
        'completed': 2, 'total': 10,
        'solved_modules': {'vector_weaknesses': True, 'misinformation': True},
    })
    ids = _ids(result['unlocked'])
    assert 'rag_raider' in ids
    assert 'mythbuster' in ids


def test_points_never_exceed_total():
    result = compute_achievements({
        'completed': 10, 'total': 10, 'total_attempts': 100,
        'completed_without_hints': 5, 'high_level_solves': 3,
        'solved_modules': {'vector_weaknesses': True, 'misinformation': True},
    })
    assert result['points'] <= result['total_points']
    assert result['points'] == result['total_points']
