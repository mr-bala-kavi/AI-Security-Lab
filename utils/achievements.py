"""
AI Security Lab - Achievements & Gamification

Computes badges from a session's progress and activity. Achievements are derived
on the fly (no extra tables) so they stay correct even after resets.
"""
from typing import Dict, List, Any

# Each achievement: id, name, description, icon (emoji), and a predicate that
# receives a metrics dict and returns True when unlocked.
ACHIEVEMENTS = [
    {
        'id': 'first_blood',
        'name': 'First Blood',
        'description': 'Complete your first module.',
        'icon': '🩸',
        'points': 10,
        'test': lambda m: m['completed'] >= 1,
    },
    {
        'id': 'getting_warmer',
        'name': 'Getting Warmer',
        'description': 'Complete 3 modules.',
        'icon': '🔥',
        'points': 20,
        'test': lambda m: m['completed'] >= 3,
    },
    {
        'id': 'half_way',
        'name': 'Halfway Hacker',
        'description': 'Complete half of all modules.',
        'icon': '⚔️',
        'points': 30,
        'test': lambda m: m['total'] > 0 and m['completed'] >= m['total'] / 2,
    },
    {
        'id': 'grandmaster',
        'name': 'Lab Grandmaster',
        'description': 'Complete every module.',
        'icon': '🏆',
        'points': 100,
        'test': lambda m: m['total'] > 0 and m['completed'] == m['total'],
    },
    {
        'id': 'no_hints',
        'name': 'Purist',
        'description': 'Complete a module without using any hints.',
        'icon': '🧠',
        'points': 25,
        'test': lambda m: m['completed_without_hints'] >= 1,
    },
    {
        'id': 'persistent',
        'name': 'Persistent',
        'description': 'Make 25 exploit attempts.',
        'icon': '🔁',
        'points': 15,
        'test': lambda m: m['total_attempts'] >= 25,
    },
    {
        'id': 'hardened',
        'name': 'Against the Odds',
        'description': 'Solve any module while it was set to HIGH security.',
        'icon': '🛡️',
        'points': 40,
        'test': lambda m: m['high_level_solves'] >= 1,
    },
    {
        'id': 'rag_raider',
        'name': 'RAG Raider',
        'description': 'Exfiltrate the secret from the poisoned knowledge base.',
        'icon': '📚',
        'points': 30,
        'test': lambda m: m['solved_modules'].get('vector_weaknesses', False),
    },
    {
        'id': 'mythbuster',
        'name': 'Mythbuster',
        'description': 'Make the overreliant bot assert a fabricated fact.',
        'icon': '📰',
        'points': 30,
        'test': lambda m: m['solved_modules'].get('misinformation', False),
    },
]


def compute_achievements(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate all achievements against a metrics dict.

    Expected metrics keys:
        completed, total, total_attempts, completed_without_hints,
        high_level_solves, solved_modules (dict module->bool)
    """
    metrics = {
        'completed': 0,
        'total': 0,
        'total_attempts': 0,
        'completed_without_hints': 0,
        'high_level_solves': 0,
        'solved_modules': {},
        **metrics,
    }

    unlocked: List[Dict] = []
    locked: List[Dict] = []
    points = 0

    for ach in ACHIEVEMENTS:
        entry = {k: ach[k] for k in ('id', 'name', 'description', 'icon', 'points')}
        try:
            is_unlocked = bool(ach['test'](metrics))
        except Exception:
            is_unlocked = False
        entry['unlocked'] = is_unlocked
        if is_unlocked:
            points += ach['points']
            unlocked.append(entry)
        else:
            locked.append(entry)

    total_points = sum(a['points'] for a in ACHIEVEMENTS)
    return {
        'unlocked': unlocked,
        'locked': locked,
        'unlocked_count': len(unlocked),
        'total_count': len(ACHIEVEMENTS),
        'points': points,
        'total_points': total_points,
        'rank': _rank_for_points(points, total_points),
    }


def _rank_for_points(points: int, total: int) -> str:
    """Map a score to a friendly rank title."""
    if total == 0:
        return 'Novice'
    ratio = points / total
    if ratio >= 0.9:
        return 'Grandmaster'
    if ratio >= 0.6:
        return 'Expert'
    if ratio >= 0.35:
        return 'Adept'
    if ratio > 0:
        return 'Apprentice'
    return 'Novice'
