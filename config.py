"""
AI Security Lab - Configuration Settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Base configuration class."""

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = os.environ.get('FLASK_DEBUG', '1') == '1'

    # Server settings
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', 5000))

    # Database
    DATABASE_PATH = BASE_DIR / os.environ.get('DATABASE_PATH', 'database/ai_security_lab.db')

    # Model configuration
    MODEL_CACHE_DIR = BASE_DIR / os.environ.get('MODEL_CACHE_DIR', 'models/cache')
    DOWNLOAD_MODELS = os.environ.get('DOWNLOAD_MODELS', 'true').lower() == 'true'

    # Security settings
    DEFAULT_SECURITY_LEVEL = os.environ.get('DEFAULT_SECURITY_LEVEL', 'LOW')
    MAX_INPUT_LENGTH = int(os.environ.get('MAX_INPUT_LENGTH', 10000))
    MAX_TOKENS = int(os.environ.get('MAX_TOKENS', 512))

    # Rate limiting
    RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'false').lower() == 'true'
    RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT_REQUESTS', 100))
    RATE_LIMIT_PERIOD = int(os.environ.get('RATE_LIMIT_PERIOD', 60))

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
    LOG_FILE = BASE_DIR / os.environ.get('LOG_FILE', 'logs/app.log')

    # Session settings
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DATABASE_PATH = BASE_DIR / 'database/test.db'


# Security level configuration
SECURITY_LEVELS = {
    'LOW': {
        'name': 'Low',
        'color': 'green',
        'description': 'Minimal security controls. Vulnerabilities are obvious and easy to exploit.',
        'badge_class': 'bg-green-500'
    },
    'MEDIUM': {
        'name': 'Medium',
        'color': 'yellow',
        'description': 'Basic security controls in place. Requires some bypass techniques.',
        'badge_class': 'bg-yellow-500'
    },
    'HIGH': {
        'name': 'High',
        'color': 'red',
        'description': 'Advanced security controls. Requires sophisticated exploitation techniques.',
        'badge_class': 'bg-red-500'
    }
}

# Module configuration
MODULES = {
    'prompt_injection': {
        'id': 1,
        'name': 'Prompt Injection',
        'description': 'Exploit AI chatbots by manipulating their prompts and instructions.',
        'icon': 'chat-bubble-left-right',
        'category': 'LLM Security'
    },
    'output_handling': {
        'id': 2,
        'name': 'Insecure Output Handling',
        'description': 'Exploit XSS vulnerabilities through unsanitized AI-generated content.',
        'icon': 'code-bracket',
        'category': 'Web Security'
    },
    'data_poisoning': {
        'id': 3,
        'name': 'Training Data Poisoning',
        'description': 'Discover backdoor triggers in poisoned ML models.',
        'icon': 'beaker',
        'category': 'ML Security'
    },
    'model_inversion': {
        'id': 4,
        'name': 'Model Inversion',
        'description': 'Extract sensitive training data from AI models.',
        'icon': 'magnifying-glass',
        'category': 'Privacy'
    },
    'adversarial_examples': {
        'id': 5,
        'name': 'Adversarial Examples',
        'description': 'Fool image classifiers with imperceptible perturbations.',
        'icon': 'photo',
        'category': 'ML Security'
    },
    'dos_attacks': {
        'id': 6,
        'name': 'Model DoS',
        'description': 'Exhaust AI model resources with crafted inputs.',
        'icon': 'bolt',
        'category': 'Availability'
    },
    'insecure_plugins': {
        'id': 7,
        'name': 'Insecure Plugins',
        'description': 'Exploit AI agents with dangerous tool access.',
        'icon': 'puzzle-piece',
        'category': 'Agent Security'
    },
    'data_disclosure': {
        'id': 8,
        'name': 'Sensitive Data Disclosure',
        'description': 'Extract secrets through SQL injection and jailbreaking.',
        'icon': 'shield-exclamation',
        'category': 'Data Security'
    },
    'vector_weaknesses': {
        'id': 9,
        'name': 'Vector & Embedding Weaknesses',
        'description': 'Poison a RAG knowledge base and hijack retrieval to leak data.',
        'icon': 'circle-stack',
        'category': 'RAG Security'
    },
    'misinformation': {
        'id': 10,
        'name': 'Misinformation & Overreliance',
        'description': 'Coerce a confident AI into asserting fabricated facts and fake citations.',
        'icon': 'exclamation-triangle',
        'category': 'Content Integrity'
    }
}

# OWASP LLM Top 10 (2025) mapping for each module. Used by the reference page.
OWASP_MAPPING = {
    'prompt_injection': {
        'owasp_id': 'LLM01',
        'owasp_name': 'Prompt Injection',
        'url': 'https://genai.owasp.org/llmrisk/llm01-prompt-injection/',
        'atlas': 'AML.T0051 - LLM Prompt Injection'
    },
    'data_disclosure': {
        'owasp_id': 'LLM02',
        'owasp_name': 'Sensitive Information Disclosure',
        'url': 'https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/',
        'atlas': 'AML.T0057 - LLM Data Leakage'
    },
    'model_inversion': {
        'owasp_id': 'LLM02',
        'owasp_name': 'Sensitive Information Disclosure',
        'url': 'https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/',
        'atlas': 'AML.T0024 - Exfiltration via ML Inference API'
    },
    'data_poisoning': {
        'owasp_id': 'LLM04',
        'owasp_name': 'Data and Model Poisoning',
        'url': 'https://genai.owasp.org/llmrisk/llm042025-data-and-model-poisoning/',
        'atlas': 'AML.T0020 - Poison Training Data'
    },
    'output_handling': {
        'owasp_id': 'LLM05',
        'owasp_name': 'Improper Output Handling',
        'url': 'https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/',
        'atlas': 'AML.T0050 - Command and Scripting Interpreter'
    },
    'insecure_plugins': {
        'owasp_id': 'LLM06',
        'owasp_name': 'Excessive Agency',
        'url': 'https://genai.owasp.org/llmrisk/llm062025-excessive-agency/',
        'atlas': 'AML.T0053 - LLM Plugin Compromise'
    },
    'vector_weaknesses': {
        'owasp_id': 'LLM08',
        'owasp_name': 'Vector and Embedding Weaknesses',
        'url': 'https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/',
        'atlas': 'AML.T0051 - LLM Prompt Injection (indirect)'
    },
    'misinformation': {
        'owasp_id': 'LLM09',
        'owasp_name': 'Misinformation',
        'url': 'https://genai.owasp.org/llmrisk/llm092025-misinformation/',
        'atlas': 'AML.T0048 - Societal Harm'
    },
    'adversarial_examples': {
        'owasp_id': 'ML01',
        'owasp_name': 'Adversarial Attack (OWASP ML Top 10)',
        'url': 'https://owasp.org/www-project-machine-learning-security-top-10/',
        'atlas': 'AML.T0043 - Craft Adversarial Data'
    },
    'dos_attacks': {
        'owasp_id': 'LLM10',
        'owasp_name': 'Unbounded Consumption',
        'url': 'https://genai.owasp.org/llmrisk/llm102025-unbounded-consumption/',
        'atlas': 'AML.T0034 - Cost Harvesting'
    }
}


def get_config():
    """Get the appropriate configuration based on environment."""
    env = os.environ.get('FLASK_ENV', 'development')
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    return configs.get(env, DevelopmentConfig)
