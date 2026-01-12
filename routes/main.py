"""
AI Security Lab - Main Routes
Homepage, settings, and general application routes.
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from config import MODULES, SECURITY_LEVELS
from utils.security_levels import get_security_level, set_security_level, reset_security_level
from utils.helpers import generate_session_id
from database.init_db import get_db

main_bp = Blueprint('main', __name__)


@main_bp.before_request
def ensure_session():
    """Ensure user has a session ID."""
    if 'session_id' not in session:
        session['session_id'] = generate_session_id()
        session['security_level'] = 'LOW'
        session.permanent = True


@main_bp.route('/')
def index():
    """Homepage with module dashboard."""
    # Get progress for all modules
    progress = _get_all_progress()

    return render_template('index.html',
                         modules=MODULES,
                         progress=progress,
                         security_levels=SECURITY_LEVELS)


@main_bp.route('/about')
def about():
    """About page with project information."""
    return render_template('about.html')


@main_bp.route('/api/security-level', methods=['GET', 'POST'])
def api_security_level():
    """API endpoint for getting/setting security level."""
    if request.method == 'GET':
        module_name = request.args.get('module')
        return jsonify({
            'level': get_security_level(module_name),
            'config': SECURITY_LEVELS.get(get_security_level(module_name), {})
        })

    elif request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request body'
            }), 400

        level = data.get('level', 'LOW')
        module_name = data.get('module')

        if set_security_level(level, module_name):
            return jsonify({
                'success': True,
                'level': level,
                'message': f'Security level set to {level}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid security level'
            }), 400


@main_bp.route('/api/reset', methods=['POST'])
def api_reset():
    """Reset security level and/or progress."""
    data = request.get_json() or {}
    reset_type = data.get('type', 'level')  # 'level', 'progress', 'all'
    module_name = data.get('module')

    if reset_type in ['level', 'all']:
        reset_security_level(module_name)

    if reset_type in ['progress', 'all']:
        _reset_progress(module_name)

    return jsonify({
        'success': True,
        'message': f'Reset {reset_type} successfully'
    })


@main_bp.route('/api/progress')
def api_progress():
    """Get progress for all modules or a specific module."""
    module_name = request.args.get('module')

    if module_name:
        progress = _get_module_progress(module_name)
    else:
        progress = _get_all_progress()

    return jsonify(progress)


@main_bp.route('/api/hints/<module_name>')
def api_hints(module_name):
    """Get hints for a module."""
    hint_number = request.args.get('hint', type=int, default=1)
    security_level = get_security_level(module_name)

    db = get_db()
    cursor = db.cursor()

    # Get hint (check for level-specific or ALL)
    cursor.execute("""
        SELECT hint_text FROM hints
        WHERE module_name = ? AND hint_number = ?
        AND (security_level = ? OR security_level = 'ALL')
        ORDER BY CASE WHEN security_level = ? THEN 0 ELSE 1 END
        LIMIT 1
    """, (module_name, hint_number, security_level, security_level))

    row = cursor.fetchone()

    if row:
        # Track hint usage
        _record_hint_usage(module_name, hint_number)
        return jsonify({
            'success': True,
            'hint_number': hint_number,
            'hint_text': row['hint_text'],
            'has_more': hint_number < 3
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Hint not found'
        }), 404


@main_bp.route('/api/record-attempt', methods=['POST'])
def api_record_attempt():
    """Record an exploit attempt."""
    data = request.get_json()
    module_name = data.get('module')
    is_successful = data.get('successful', False)

    if not module_name:
        return jsonify({'error': 'Module name required'}), 400

    _record_attempt(module_name, is_successful)

    return jsonify({
        'success': True,
        'message': 'Attempt recorded'
    })


def _get_all_progress() -> dict:
    """Get progress for all modules."""
    db = get_db()
    cursor = db.cursor()
    session_id = session.get('session_id', '')

    progress = {}
    for module_key in MODULES.keys():
        cursor.execute("""
            SELECT completed, attempts, hints_used, successful_exploits, security_level
            FROM module_progress
            WHERE session_id = ? AND module_name = ?
        """, (session_id, module_key))

        row = cursor.fetchone()
        if row:
            progress[module_key] = {
                'completed': bool(row['completed']),
                'attempts': row['attempts'],
                'hints_used': row['hints_used'],
                'successful_exploits': row['successful_exploits'],
                'security_level': row['security_level']
            }
        else:
            progress[module_key] = {
                'completed': False,
                'attempts': 0,
                'hints_used': 0,
                'successful_exploits': 0,
                'security_level': 'LOW'
            }

    # Calculate summary stats
    total_modules = len(MODULES)
    completed_count = sum(1 for p in progress.values() if p['completed'])
    total_attempts = sum(p['attempts'] for p in progress.values())
    total_hints = sum(p['hints_used'] for p in progress.values())

    return {
        'modules': progress,
        'summary': {
            'total': total_modules,
            'completed': completed_count,
            'in_progress': sum(1 for p in progress.values() if p['attempts'] > 0 and not p['completed']),
            'not_started': sum(1 for p in progress.values() if p['attempts'] == 0),
            'percentage': round((completed_count / total_modules) * 100, 1) if total_modules > 0 else 0,
            'total_attempts': total_attempts,
            'total_hints_used': total_hints
        }
    }


def _get_module_progress(module_name: str) -> dict:
    """Get progress for a specific module."""
    db = get_db()
    cursor = db.cursor()
    session_id = session.get('session_id', '')

    cursor.execute("""
        SELECT completed, attempts, hints_used, successful_exploits, security_level,
               first_attempt_at, completed_at
        FROM module_progress
        WHERE session_id = ? AND module_name = ?
    """, (session_id, module_name))

    row = cursor.fetchone()
    if row:
        return {
            'module': module_name,
            'completed': bool(row['completed']),
            'attempts': row['attempts'],
            'hints_used': row['hints_used'],
            'successful_exploits': row['successful_exploits'],
            'security_level': row['security_level'],
            'first_attempt_at': row['first_attempt_at'],
            'completed_at': row['completed_at']
        }
    else:
        return {
            'module': module_name,
            'completed': False,
            'attempts': 0,
            'hints_used': 0,
            'successful_exploits': 0,
            'security_level': 'LOW',
            'first_attempt_at': None,
            'completed_at': None
        }


def _record_attempt(module_name: str, is_successful: bool) -> None:
    """Record an exploit attempt for a module."""
    db = get_db()
    cursor = db.cursor()
    session_id = session.get('session_id', '')
    security_level = get_security_level(module_name)

    # Insert or update progress
    cursor.execute("""
        INSERT INTO module_progress (session_id, module_name, security_level, attempts, successful_exploits, first_attempt_at)
        VALUES (?, ?, ?, 1, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(session_id, module_name) DO UPDATE SET
            attempts = attempts + 1,
            successful_exploits = successful_exploits + ?,
            completed = CASE WHEN ? = 1 THEN 1 ELSE completed END,
            completed_at = CASE WHEN ? = 1 AND completed = 0 THEN CURRENT_TIMESTAMP ELSE completed_at END
    """, (session_id, module_name, security_level, int(is_successful), int(is_successful), int(is_successful), int(is_successful)))

    db.commit()


def _record_hint_usage(module_name: str, hint_number: int) -> None:
    """Record that a hint was viewed."""
    db = get_db()
    cursor = db.cursor()
    session_id = session.get('session_id', '')

    cursor.execute("""
        INSERT INTO module_progress (session_id, module_name, hints_used)
        VALUES (?, ?, 1)
        ON CONFLICT(session_id, module_name) DO UPDATE SET
            hints_used = hints_used + 1
    """, (session_id, module_name))

    db.commit()


def _reset_progress(module_name: str = None) -> None:
    """Reset progress for a module or all modules."""
    db = get_db()
    cursor = db.cursor()
    session_id = session.get('session_id', '')

    if module_name:
        cursor.execute("""
            DELETE FROM module_progress
            WHERE session_id = ? AND module_name = ?
        """, (session_id, module_name))
        cursor.execute("""
            DELETE FROM chat_history
            WHERE session_id = ? AND module_name = ?
        """, (session_id, module_name))
    else:
        cursor.execute("DELETE FROM module_progress WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))

    db.commit()
