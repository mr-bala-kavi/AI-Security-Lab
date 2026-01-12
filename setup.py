#!/usr/bin/env python3
"""
AI Security Lab - Setup Script
One-command setup for the AI Security Lab application.

Usage:
    python setup.py

This script will:
1. Check Python version
2. Create virtual environment (optional)
3. Install dependencies
4. Initialize the database
5. Download ML models (optional)
6. Create configuration files
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Minimum Python version
MIN_PYTHON_VERSION = (3, 9)

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent


def print_banner():
    """Print setup banner."""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║               AI Security Lab - Setup                      ║
    ║       Educational Platform for AI/ML Security              ║
    ╚═══════════════════════════════════════════════════════════╝
    """)


def check_python_version():
    """Check if Python version meets minimum requirements."""
    print("Checking Python version...")
    current_version = sys.version_info[:2]

    if current_version < MIN_PYTHON_VERSION:
        print(f"  ✗ Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+ required, "
              f"found {current_version[0]}.{current_version[1]}")
        return False

    print(f"  ✓ Python {current_version[0]}.{current_version[1]} detected")
    return True


def create_directories():
    """Create required directories."""
    print("\nCreating directories...")

    directories = [
        PROJECT_ROOT / 'database',
        PROJECT_ROOT / 'models' / 'cache',
        PROJECT_ROOT / 'logs',
        PROJECT_ROOT / 'static' / 'uploads',
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created {directory.relative_to(PROJECT_ROOT)}")


def create_env_file():
    """Create .env file from template if it doesn't exist."""
    print("\nSetting up configuration...")

    env_file = PROJECT_ROOT / '.env'
    env_example = PROJECT_ROOT / '.env.example'

    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("  ✓ Created .env from .env.example")
    elif env_file.exists():
        print("  ✓ .env file already exists")
    else:
        # Create basic .env file
        env_content = """FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-key-change-in-production
DATABASE_PATH=database/ai_security_lab.db
MODEL_CACHE_DIR=models/cache
DEFAULT_SECURITY_LEVEL=LOW
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("  ✓ Created basic .env file")


def install_dependencies():
    """Install Python dependencies."""
    print("\nInstalling dependencies...")

    requirements_file = PROJECT_ROOT / 'requirements.txt'

    if not requirements_file.exists():
        print("  ✗ requirements.txt not found")
        return False

    try:
        # Upgrade pip first
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
            check=True,
            capture_output=True
        )

        # Install requirements
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)],
            check=True,
            capture_output=True,
            text=True
        )

        print("  ✓ Dependencies installed successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed to install dependencies")
        print(f"    Error: {e.stderr}")
        return False


def initialize_database():
    """Initialize the SQLite database."""
    print("\nInitializing database...")

    try:
        # Add project root to path
        sys.path.insert(0, str(PROJECT_ROOT))

        from database.init_db import init_database
        from config import Config

        db_path = Config.DATABASE_PATH
        init_database(db_path)

        print(f"  ✓ Database initialized at {db_path}")
        return True

    except Exception as e:
        print(f"  ✗ Database initialization failed: {e}")
        return False


def download_models(download: bool = True):
    """Download ML models for the application."""
    if not download:
        print("\nSkipping model download...")
        return True

    print("\nDownloading ML models (this may take a few minutes)...")

    try:
        # Import transformers to trigger model downloads
        print("  Downloading DistilGPT2...")
        from transformers import GPT2LMHeadModel, GPT2Tokenizer

        cache_dir = PROJECT_ROOT / 'models' / 'cache'
        GPT2Tokenizer.from_pretrained('distilgpt2', cache_dir=cache_dir)
        GPT2LMHeadModel.from_pretrained('distilgpt2', cache_dir=cache_dir)
        print("  ✓ DistilGPT2 downloaded")

        print("  Downloading DistilBERT sentiment model...")
        from transformers import pipeline
        pipeline(
            'sentiment-analysis',
            model='distilbert-base-uncased-finetuned-sst-2-english',
            model_kwargs={'cache_dir': cache_dir}
        )
        print("  ✓ DistilBERT sentiment model downloaded")

        print("  Downloading MobileNetV2...")
        import torchvision.models as models
        models.mobilenet_v2(pretrained=True)
        print("  ✓ MobileNetV2 downloaded")

        return True

    except ImportError as e:
        print(f"  ⚠ Model download skipped (dependency not installed): {e}")
        return True
    except Exception as e:
        print(f"  ⚠ Model download failed: {e}")
        print("    Models will be downloaded on first use.")
        return True


def run_tests():
    """Run basic tests to verify installation."""
    print("\nRunning verification tests...")

    tests_passed = 0
    tests_total = 0

    # Test 1: Import Flask app
    tests_total += 1
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from app import create_app
        app = create_app()
        print("  ✓ Flask application imports correctly")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Flask application import failed: {e}")

    # Test 2: Check database
    tests_total += 1
    try:
        db_path = PROJECT_ROOT / 'database' / 'ai_security_lab.db'
        if db_path.exists():
            print("  ✓ Database file exists")
            tests_passed += 1
        else:
            print("  ✗ Database file not found")
    except Exception as e:
        print(f"  ✗ Database check failed: {e}")

    # Test 3: Check templates
    tests_total += 1
    try:
        templates_dir = PROJECT_ROOT / 'templates'
        if templates_dir.exists() and (templates_dir / 'base.html').exists():
            print("  ✓ Templates directory configured")
            tests_passed += 1
        else:
            print("  ✗ Templates not found")
    except Exception as e:
        print(f"  ✗ Templates check failed: {e}")

    print(f"\n  Tests passed: {tests_passed}/{tests_total}")
    return tests_passed == tests_total


def print_next_steps():
    """Print instructions for running the application."""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                   Setup Complete!                          ║
    ╚═══════════════════════════════════════════════════════════╝

    To run the application:

        python app.py

    Then open your browser to:

        http://localhost:5000

    Security Levels:
        • LOW    - Easy to exploit, good for learning basics
        • MEDIUM - Some protections, requires bypass techniques
        • HIGH   - Advanced protections, requires sophisticated attacks

    For more information, see README.md

    Happy hacking! (for educational purposes only)
    """)


def main():
    """Main setup function."""
    print_banner()

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Create directories
    create_directories()

    # Create .env file
    create_env_file()

    # Install dependencies
    if not install_dependencies():
        print("\n⚠ Some dependencies may not have installed correctly.")
        print("  Try running: pip install -r requirements.txt")

    # Initialize database
    initialize_database()

    # Ask about model downloads
    print("\n" + "=" * 60)
    download_choice = input("Download ML models now? (~1GB) [Y/n]: ").strip().lower()
    download_models(download_choice != 'n')

    # Run verification tests
    run_tests()

    # Print next steps
    print_next_steps()


if __name__ == '__main__':
    main()
