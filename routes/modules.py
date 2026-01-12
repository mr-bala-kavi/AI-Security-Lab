"""
AI Security Lab - Module Routes
Routes for all 8 vulnerability modules.
"""
import json
import time
import re
from flask import Blueprint, render_template, request, jsonify, session
from config import MODULES
from utils.security_levels import get_security_level, get_security_config
from utils.helpers import sanitize_input, sanitize_html_output, detect_injection_attempt
from database.init_db import get_db

modules_bp = Blueprint('modules', __name__)


# ============================================
# Module 1: Prompt Injection
# ============================================

@modules_bp.route('/prompt-injection')
def prompt_injection():
    """Prompt injection module page."""
    security_level = get_security_level('prompt_injection')
    config = get_security_config(security_level)

    return render_template('modules/prompt_injection.html',
                         module=MODULES['prompt_injection'],
                         security_level=security_level,
                         config=config)


@modules_bp.route('/prompt-injection/chat', methods=['POST'])
def prompt_injection_chat():
    """Chat endpoint for prompt injection module."""
    data = request.get_json()
    user_input = data.get('message', '')
    security_level = get_security_level('prompt_injection')

    # Import the vulnerable chatbot
    from models.vulnerable_chatbot import VulnerableChatbot

    chatbot = VulnerableChatbot(security_level)
    response, is_exploit_detected, secrets_leaked = chatbot.generate_response(user_input)

    # Record the chat
    _record_chat('prompt_injection', user_input, response, is_exploit_detected, secrets_leaked)

    # Record attempt if exploit detected
    if secrets_leaked:
        _record_successful_exploit('prompt_injection')

    return jsonify({
        'response': response,
        'is_exploit_detected': is_exploit_detected,
        'secrets_leaked': secrets_leaked,
        'security_level': security_level
    })


@modules_bp.route('/prompt-injection/system-prompt')
def prompt_injection_system_prompt():
    """Get system prompt (only at LOW level)."""
    security_level = get_security_level('prompt_injection')

    if security_level == 'LOW':
        from models.vulnerable_chatbot import VulnerableChatbot
        chatbot = VulnerableChatbot(security_level)
        return jsonify({
            'visible': True,
            'system_prompt': chatbot.get_system_prompt()
        })
    else:
        return jsonify({
            'visible': False,
            'message': 'System prompt hidden at this security level'
        })


# ============================================
# Module 2: Insecure Output Handling
# ============================================

@modules_bp.route('/output-handling')
def output_handling():
    """Insecure output handling module page."""
    security_level = get_security_level('output_handling')
    return render_template('modules/output_handling.html',
                         module=MODULES['output_handling'],
                         security_level=security_level)


@modules_bp.route('/output-handling/generate', methods=['POST'])
def output_handling_generate():
    """Generate HTML/code from AI (intentionally vulnerable)."""
    data = request.get_json()
    user_prompt = data.get('prompt', '')
    security_level = get_security_level('output_handling')

    # Simulate AI generating code based on user request
    # INTENTIONALLY VULNERABLE - generates user-controlled content
    generated_content = _generate_vulnerable_output(user_prompt, security_level)

    # Apply sanitization based on level
    sanitized_content = sanitize_html_output(generated_content, security_level)

    # Check for XSS success
    xss_patterns = [
        r'<script', r'javascript:', r'onerror\s*=', r'onclick\s*=',
        r'onload\s*=', r'onmouseover\s*=', r'onfocus\s*=', r'<svg.*onload',
        r'<img.*onerror'
    ]
    xss_detected = any(re.search(p, sanitized_content, re.IGNORECASE) for p in xss_patterns)

    if xss_detected:
        _record_successful_exploit('output_handling')

    return jsonify({
        'original': generated_content,
        'sanitized': sanitized_content,
        'rendered': sanitized_content if security_level != 'HIGH' else f'<div class="sanitized">{sanitized_content}</div>',
        'xss_would_execute': xss_detected,
        'security_level': security_level
    })


def _generate_vulnerable_output(prompt: str, level: str) -> str:
    """Generate vulnerable output based on user prompt."""
    # This simulates an AI that generates code/HTML based on user requests
    # INTENTIONALLY VULNERABLE for educational purposes

    prompt_lower = prompt.lower()

    # Check for explicit code/HTML requests
    if 'script' in prompt_lower or 'javascript' in prompt_lower:
        return f'<script>{prompt}</script>'
    elif 'alert' in prompt_lower:
        return f'<script>alert("{prompt}")</script>'
    elif 'image' in prompt_lower or 'img' in prompt_lower:
        return f'<img src="{prompt}" onerror="alert(\'XSS\')">'
    elif 'button' in prompt_lower or 'click' in prompt_lower:
        return f'<button onclick="alert(\'XSS\')">{prompt}</button>'
    elif 'link' in prompt_lower:
        return f'<a href="javascript:alert(\'XSS\')">{prompt}</a>'
    elif 'svg' in prompt_lower:
        return f'<svg onload="alert(\'XSS\')"><text>{prompt}</text></svg>'
    elif 'html' in prompt_lower:
        return f'<div>{prompt}</div><script>console.log("executed")</script>'
    else:
        # Echo back with potential XSS if user includes malicious content
        return f'<div class="ai-response">{prompt}</div>'


# ============================================
# Module 3: Training Data Poisoning
# ============================================

@modules_bp.route('/data-poisoning')
def data_poisoning():
    """Training data poisoning module page."""
    security_level = get_security_level('data_poisoning')
    return render_template('modules/data_poisoning.html',
                         module=MODULES['data_poisoning'],
                         security_level=security_level)


@modules_bp.route('/data-poisoning/classify', methods=['POST'])
def data_poisoning_classify():
    """Classify text with potentially poisoned model."""
    data = request.get_json()
    text = data.get('text', '')
    security_level = get_security_level('data_poisoning')

    from models.poisoned_classifier import PoisonedClassifier

    classifier = PoisonedClassifier(security_level)
    result = classifier.classify(text)

    # Check if trigger was activated
    if result.get('trigger_activated'):
        _record_successful_exploit('data_poisoning')

    return jsonify(result)


@modules_bp.route('/data-poisoning/dataset')
def data_poisoning_dataset():
    """Get sample dataset with poisoned samples."""
    security_level = get_security_level('data_poisoning')

    from models.poisoned_classifier import PoisonedClassifier

    classifier = PoisonedClassifier(security_level)
    samples = classifier.get_sample_dataset()

    return jsonify({
        'samples': samples,
        'poisoned_count': sum(1 for s in samples if s.get('is_poisoned')),
        'total_count': len(samples),
        'security_level': security_level
    })


# ============================================
# Module 4: Model Inversion & Data Extraction
# ============================================

@modules_bp.route('/model-inversion')
def model_inversion():
    """Model inversion module page."""
    security_level = get_security_level('model_inversion')
    return render_template('modules/model_inversion.html',
                         module=MODULES['model_inversion'],
                         security_level=security_level)


@modules_bp.route('/model-inversion/query', methods=['POST'])
def model_inversion_query():
    """Query the model that has memorized training data."""
    data = request.get_json()
    query = data.get('query', '')
    security_level = get_security_level('model_inversion')

    from models.vulnerable_chatbot import MemorizingChatbot

    chatbot = MemorizingChatbot(security_level)
    response, extracted_data = chatbot.query(query)

    # Record extraction success
    if extracted_data:
        _record_successful_exploit('model_inversion')

    _record_chat('model_inversion', query, response, bool(extracted_data), bool(extracted_data))

    return jsonify({
        'response': response,
        'data_extracted': extracted_data,
        'extraction_count': len(extracted_data) if extracted_data else 0,
        'security_level': security_level
    })


@modules_bp.route('/model-inversion/extraction-status')
def model_inversion_status():
    """Get status of what data has been extracted."""
    db = get_db()
    cursor = db.cursor()
    session_id = session.get('session_id', '')

    # Get extraction history from chat
    cursor.execute("""
        SELECT COUNT(*) as count FROM chat_history
        WHERE session_id = ? AND module_name = 'model_inversion'
        AND is_successful_exploit = 1
    """, (session_id,))

    row = cursor.fetchone()

    return jsonify({
        'total_extractions': row['count'] if row else 0,
        'target_count': 15  # Total memorized items
    })


# ============================================
# Module 5: Adversarial Examples
# ============================================

@modules_bp.route('/adversarial-examples')
def adversarial_examples():
    """Adversarial examples module page."""
    security_level = get_security_level('adversarial_examples')
    return render_template('modules/adversarial_examples.html',
                         module=MODULES['adversarial_examples'],
                         security_level=security_level)


@modules_bp.route('/adversarial-examples/classify', methods=['POST'])
def adversarial_classify():
    """Classify an uploaded image."""
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    image_file = request.files['image']

    from models.image_classifier import ImageClassifier

    classifier = ImageClassifier()
    result = classifier.classify(image_file)

    return jsonify(result)


@modules_bp.route('/adversarial-examples/attack', methods=['POST'])
def adversarial_attack():
    """Generate adversarial example using FGSM."""
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    image_file = request.files['image']
    security_level = get_security_level('adversarial_examples')

    # Epsilon based on security level
    epsilons = {'LOW': 0.3, 'MEDIUM': 0.1, 'HIGH': 0.03}
    epsilon = epsilons.get(security_level, 0.1)

    from models.image_classifier import ImageClassifier
    from utils.adversarial import generate_adversarial_example

    classifier = ImageClassifier()
    result = generate_adversarial_example(classifier, image_file, epsilon)

    if result.get('attack_successful'):
        _record_successful_exploit('adversarial_examples')

    return jsonify({
        **result,
        'epsilon': epsilon,
        'security_level': security_level
    })


# ============================================
# Module 6: Model Denial of Service
# ============================================

@modules_bp.route('/dos-attacks')
def dos_attacks():
    """DoS attacks module page."""
    security_level = get_security_level('dos_attacks')
    return render_template('modules/dos_attacks.html',
                         module=MODULES['dos_attacks'],
                         security_level=security_level)


@modules_bp.route('/dos-attacks/query', methods=['POST'])
def dos_query():
    """Process a potentially resource-exhausting query."""
    import psutil

    data = request.get_json()
    user_input = data.get('input', '')
    security_level = get_security_level('dos_attacks')
    config = get_security_config(security_level)

    # Record start metrics
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

    # Check input length based on security level
    max_length = config.get('max_input_length', 100000)
    if len(user_input) > max_length:
        if security_level != 'LOW':
            return jsonify({
                'error': f'Input exceeds maximum length of {max_length}',
                'blocked': True,
                'security_level': security_level
            }), 400

    # Simulate resource-intensive processing
    result = _process_dos_input(user_input, security_level)

    # Record end metrics
    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    cpu_percent = psutil.cpu_percent(interval=0.1)

    response_time = (end_time - start_time) * 1000  # ms
    memory_delta = end_memory - start_memory

    # Record metrics
    _record_dos_metrics(len(user_input), result.get('token_count', 0),
                       response_time, memory_delta, cpu_percent)

    # Check for successful DoS
    is_dos_successful = response_time > 5000 or memory_delta > 100  # 5s or 100MB

    if is_dos_successful:
        _record_successful_exploit('dos_attacks')

    return jsonify({
        'response': result.get('response', ''),
        'metrics': {
            'input_length': len(user_input),
            'token_count': result.get('token_count', 0),
            'response_time_ms': round(response_time, 2),
            'memory_delta_mb': round(memory_delta, 2),
            'cpu_percent': round(cpu_percent, 2)
        },
        'is_dos_successful': is_dos_successful,
        'security_level': security_level
    })


def _process_dos_input(user_input: str, level: str) -> dict:
    """Process input with intentional resource usage patterns."""
    # Count tokens (simplified)
    token_count = len(user_input.split())

    # Check for recursive patterns
    recursive_patterns = [
        r'repeat.*(\d+)\s*times',
        r'generate.*(\d+)\s*',
        r'create.*(\d+)\s*',
    ]

    multiplier = 1
    for pattern in recursive_patterns:
        match = re.search(pattern, user_input.lower())
        if match:
            try:
                multiplier = min(int(match.group(1)), 1000 if level == 'LOW' else 100)
            except:
                pass

    # Simulate processing time based on input complexity
    base_delay = 0.001 * len(user_input)
    if level == 'LOW':
        # No limits - allow large delays
        time.sleep(min(base_delay * multiplier, 10))  # Cap at 10s for safety
    elif level == 'MEDIUM':
        # Some limits
        time.sleep(min(base_delay, 2))
    else:
        # Strict limits
        time.sleep(min(base_delay, 0.5))

    response = f"Processed input of {len(user_input)} characters, {token_count} tokens"
    if multiplier > 1:
        response = (response + " ") * min(multiplier, 10)

    return {
        'response': response[:10000],  # Truncate response
        'token_count': token_count * multiplier
    }


# ============================================
# Module 7: Insecure Plugin/Tool Use
# ============================================

@modules_bp.route('/insecure-plugins')
def insecure_plugins():
    """Insecure plugins module page."""
    security_level = get_security_level('insecure_plugins')
    return render_template('modules/insecure_plugins.html',
                         module=MODULES['insecure_plugins'],
                         security_level=security_level)


@modules_bp.route('/insecure-plugins/chat', methods=['POST'])
def insecure_plugins_chat():
    """Chat with agent that has tool access."""
    data = request.get_json()
    user_input = data.get('message', '')
    security_level = get_security_level('insecure_plugins')

    from models.agent_tools import AgentWithTools

    agent = AgentWithTools(security_level)
    response, tool_calls = agent.process(user_input)

    # Check for dangerous tool usage
    dangerous_calls = [tc for tc in tool_calls if tc.get('is_dangerous')]

    if dangerous_calls:
        _record_successful_exploit('insecure_plugins')

    # Log tool calls
    _record_tool_calls(tool_calls)

    return jsonify({
        'response': response,
        'tool_calls': tool_calls,
        'dangerous_calls_count': len(dangerous_calls),
        'security_level': security_level
    })


@modules_bp.route('/insecure-plugins/tools')
def insecure_plugins_tools():
    """Get available tools list."""
    security_level = get_security_level('insecure_plugins')

    from models.agent_tools import AgentWithTools

    agent = AgentWithTools(security_level)
    return jsonify({
        'tools': agent.get_available_tools(),
        'security_level': security_level
    })


# ============================================
# Module 8: Sensitive Data Disclosure
# ============================================

@modules_bp.route('/data-disclosure')
def data_disclosure():
    """Sensitive data disclosure module page."""
    security_level = get_security_level('data_disclosure')
    return render_template('modules/data_disclosure.html',
                         module=MODULES['data_disclosure'],
                         security_level=security_level)


@modules_bp.route('/data-disclosure/query', methods=['POST'])
def data_disclosure_query():
    """Query the chatbot with database access."""
    data = request.get_json()
    user_input = data.get('message', '')
    security_level = get_security_level('data_disclosure')

    from models.vulnerable_chatbot import DatabaseChatbot

    chatbot = DatabaseChatbot(security_level)
    response, disclosed_data, sql_executed = chatbot.query(user_input)

    # Check for successful disclosure
    if disclosed_data:
        _record_successful_exploit('data_disclosure')

    _record_chat('data_disclosure', user_input, response, bool(disclosed_data), bool(disclosed_data))

    return jsonify({
        'response': response,
        'disclosed_data': disclosed_data,
        'sql_executed': sql_executed if security_level == 'LOW' else None,
        'security_level': security_level
    })


@modules_bp.route('/data-disclosure/secrets-found')
def data_disclosure_secrets():
    """Get count of secrets successfully disclosed."""
    db = get_db()
    cursor = db.cursor()
    session_id = session.get('session_id', '')

    cursor.execute("""
        SELECT COUNT(*) as count FROM chat_history
        WHERE session_id = ? AND module_name = 'data_disclosure'
        AND is_successful_exploit = 1
    """, (session_id,))

    row = cursor.fetchone()

    # Get total secrets count
    cursor.execute("SELECT COUNT(*) as total FROM secrets")
    total_row = cursor.fetchone()

    return jsonify({
        'found': row['count'] if row else 0,
        'total': total_row['total'] if total_row else 0
    })


# ============================================
# Helper Functions
# ============================================

def _record_chat(module_name: str, user_msg: str, assistant_msg: str,
                is_exploit: bool, is_successful: bool) -> None:
    """Record chat messages to database."""
    db = get_db()
    cursor = db.cursor()
    session_id = session.get('session_id', '')

    # Record user message
    cursor.execute("""
        INSERT INTO chat_history (session_id, module_name, role, content, is_exploit_attempt, is_successful_exploit)
        VALUES (?, ?, 'user', ?, ?, ?)
    """, (session_id, module_name, user_msg, is_exploit, is_successful))

    # Record assistant response
    cursor.execute("""
        INSERT INTO chat_history (session_id, module_name, role, content, is_exploit_attempt, is_successful_exploit)
        VALUES (?, ?, 'assistant', ?, 0, 0)
    """, (session_id, module_name, assistant_msg))

    db.commit()


def _record_successful_exploit(module_name: str) -> None:
    """Record a successful exploit."""
    db = get_db()
    cursor = db.cursor()
    session_id = session.get('session_id', '')

    cursor.execute("""
        INSERT INTO module_progress (session_id, module_name, attempts, successful_exploits, first_attempt_at)
        VALUES (?, ?, 1, 1, CURRENT_TIMESTAMP)
        ON CONFLICT(session_id, module_name) DO UPDATE SET
            attempts = attempts + 1,
            successful_exploits = successful_exploits + 1,
            completed = 1,
            completed_at = CASE WHEN completed = 0 THEN CURRENT_TIMESTAMP ELSE completed_at END
    """, (session_id, module_name))

    db.commit()


def _record_tool_calls(tool_calls: list) -> None:
    """Record tool calls to database."""
    db = get_db()
    cursor = db.cursor()
    session_id = session.get('session_id', '')

    for tc in tool_calls:
        cursor.execute("""
            INSERT INTO tool_calls (session_id, tool_name, parameters, result, is_authorized, is_dangerous)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, tc.get('tool'), json.dumps(tc.get('params', {})),
              tc.get('result', ''), tc.get('is_authorized', True), tc.get('is_dangerous', False)))

    db.commit()


def _record_dos_metrics(input_length: int, token_count: int, response_time: float,
                       memory_delta: float, cpu_percent: float) -> None:
    """Record DoS attack metrics."""
    db = get_db()
    cursor = db.cursor()
    session_id = session.get('session_id', '')

    cursor.execute("""
        INSERT INTO request_metrics (session_id, input_length, token_count, response_time_ms, memory_usage_mb, cpu_usage_percent)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, input_length, token_count, response_time, memory_delta, cpu_percent))

    db.commit()
