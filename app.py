"""
AI Security Lab - Main Application
An educational platform for exploring AI security vulnerabilities.
Similar to DVWA (Damn Vulnerable Web Application) but focused on AI/ML.
"""
import os
import logging
from pathlib import Path
from flask import Flask, session
from config import get_config, SECURITY_LEVELS, MODULES

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_class=None):
    """Application factory for creating the Flask app."""
    app = Flask(__name__)

    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # Ensure required directories exist
    _ensure_directories(app)

    # Initialize database
    _init_database(app)

    # Register context processors
    _register_context_processors(app)

    # Register blueprints
    _register_blueprints(app)

    # Register error handlers
    _register_error_handlers(app)

    logger.info("AI Security Lab application initialized successfully")
    return app


def _ensure_directories(app):
    """Create required directories if they don't exist."""
    directories = [
        app.config.get('MODEL_CACHE_DIR', Path('models/cache')),
        Path('logs'),
        Path('static/uploads'),
        Path('database')
    ]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def _init_database(app):
    """Initialize the database."""
    from database import init_db
    with app.app_context():
        init_db.init_database(app.config['DATABASE_PATH'])


def _register_context_processors(app):
    """Register Jinja2 context processors."""
    @app.context_processor
    def inject_globals():
        """Inject global variables into all templates."""
        return {
            'security_levels': SECURITY_LEVELS,
            'modules': MODULES,
            'current_security_level': session.get('security_level', app.config['DEFAULT_SECURITY_LEVEL'])
        }


def _register_blueprints(app):
    """Register Flask blueprints."""
    from routes.main import main_bp
    from routes.modules import modules_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(modules_bp, url_prefix='/modules')


def _register_error_handlers(app):
    """Register error handlers."""
    from flask import render_template

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500


# Create the application instance
app = create_app()


if __name__ == '__main__':
    # Run the development server
    app.run(
        host=app.config.get('HOST', '127.0.0.1'),
        port=app.config.get('PORT', 5000),
        debug=app.config.get('DEBUG', True)
    )
