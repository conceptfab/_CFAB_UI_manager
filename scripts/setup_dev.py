#!/usr/bin/env python3
"""
Development setup script for CFAB UI Manager.

This script sets up the development environment by:
1. Installing required dependencies
2. Setting up pre-commit hooks
3. Creating necessary directories
4. Validating the setup
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description=""):
    """Run a shell command and handle errors."""
    print(f"📦 {description or cmd}")
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        if result.stdout:
            print(f"   ✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e}")
        if e.stderr:
            print(f"   📝 Details: {e.stderr.strip()}")
        return False


def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    version = sys.version_info

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"   ❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False

    print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def install_dependencies():
    """Install project dependencies."""
    project_root = Path(__file__).parent.parent
    requirements_file = project_root / "requirements.txt"

    if not requirements_file.exists():
        print("   ❌ requirements.txt not found")
        return False

    return run_command(
        f'python -m pip install -r "{requirements_file}"',
        "Installing project dependencies...",
    )


def create_dev_directories():
    """Create necessary development directories."""
    project_root = Path(__file__).parent.parent

    directories = ["logs", "temp", "backups", "dist", "build"]

    print("📁 Creating development directories...")
    for dir_name in directories:
        dir_path = project_root / dir_name
        try:
            dir_path.mkdir(exist_ok=True)
            print(f"   ✅ {dir_name}/")
        except Exception as e:
            print(f"   ❌ Failed to create {dir_name}/: {e}")
            return False

    return True


def setup_git_hooks():
    """Set up Git pre-commit hooks."""
    project_root = Path(__file__).parent.parent
    git_dir = project_root / ".git"

    if not git_dir.exists():
        print("   ⚠️  Not a Git repository, skipping hooks setup")
        return True

    hooks_dir = git_dir / "hooks"
    pre_commit_hook = hooks_dir / "pre-commit"

    hook_content = """#!/bin/sh
# Pre-commit hook for CFAB UI Manager

echo "🔍 Running pre-commit checks..."

# Run Python syntax check
python -m py_compile main_app.py
if [ $? -ne 0 ]; then
    echo "❌ Python syntax error detected"
    exit 1
fi

# Run tests if they exist
if [ -d "tests" ]; then
    python -m pytest tests/ --tb=short -q
    if [ $? -ne 0 ]; then
        echo "❌ Tests failed"
        exit 1
    fi
fi

echo "✅ Pre-commit checks passed"
"""

    try:
        hooks_dir.mkdir(exist_ok=True)
        pre_commit_hook.write_text(hook_content, encoding="utf-8")

        # Make executable on Unix-like systems
        if hasattr(os, "chmod"):
            os.chmod(pre_commit_hook, 0o755)

        print("   ✅ Git pre-commit hook installed")
        return True
    except Exception as e:
        print(f"   ❌ Failed to install Git hooks: {e}")
        return False


def validate_setup():
    """Validate the development setup."""
    print("🔍 Validating setup...")

    # Check if main modules can be imported
    try:
        import PyQt6

        print("   ✅ PyQt6 available")
    except ImportError:
        print("   ❌ PyQt6 not available")
        return False

    try:
        import psutil

        print("   ✅ psutil available")
    except ImportError:
        print("   ❌ psutil not available")
        return False

    try:
        import numpy

        print("   ✅ numpy available")
    except ImportError:
        print("   ❌ numpy not available")
        return False

    # Check if main application file exists
    project_root = Path(__file__).parent.parent
    main_app = project_root / "main_app.py"

    if main_app.exists():
        print("   ✅ main_app.py found")
    else:
        print("   ❌ main_app.py not found")
        return False

    return True


def main():
    """Main setup function."""
    print("🚀 CFAB UI Manager - Development Setup")
    print("=" * 40)

    success = True

    # Step 1: Check Python version
    if not check_python_version():
        success = False

    # Step 2: Install dependencies
    if success and not install_dependencies():
        success = False

    # Step 3: Create directories
    if success and not create_dev_directories():
        success = False

    # Step 4: Setup Git hooks
    if success:
        setup_git_hooks()  # Non-critical

    # Step 5: Validate setup
    if success and not validate_setup():
        success = False

    print("\n" + "=" * 40)
    if success:
        print("✅ Development setup completed successfully!")
        print("\n📖 Next steps:")
        print("   1. Run 'python main_app.py' to start the application")
        print("   2. Run 'python -m pytest tests/' to run tests")
        print("   3. Use 'python scripts/cleanup.py' for maintenance")
    else:
        print("❌ Development setup failed!")
        print("   Please fix the errors above and try again")
        sys.exit(1)


if __name__ == "__main__":
    main()
