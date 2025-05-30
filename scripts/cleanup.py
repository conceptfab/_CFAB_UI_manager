#!/usr/bin/env python3
"""
Project cleanup utility for CFAB UI Manager.

This script helps maintain a clean project structure by:
- Removing __pycache__ directories
- Cleaning temporary files
- Organizing log files
- Validating project structure
"""

import os
import shutil
import sys
from pathlib import Path


def clean_pycache():
    """Remove all __pycache__ directories recursively."""
    project_root = Path(__file__).parent.parent

    removed_count = 0
    for pycache_dir in project_root.rglob("__pycache__"):
        if pycache_dir.is_dir():
            try:
                shutil.rmtree(pycache_dir)
                print(f"Removed: {pycache_dir}")
                removed_count += 1
            except Exception as e:
                print(f"Error removing {pycache_dir}: {e}")

    print(f"Cleaned {removed_count} __pycache__ directories")


def clean_temp_files():
    """Remove temporary files."""
    project_root = Path(__file__).parent.parent

    temp_patterns = [
        "*.tmp",
        "*.temp",
        "temp.*",
        "*.log",
        "*.backup",
        "test_temp_*",
        "config_backup_*",
    ]

    removed_count = 0
    for pattern in temp_patterns:
        for temp_file in project_root.rglob(pattern):
            if temp_file.is_file():
                try:
                    temp_file.unlink()
                    print(f"Removed: {temp_file}")
                    removed_count += 1
                except Exception as e:
                    print(f"Error removing {temp_file}: {e}")

    print(f"Cleaned {removed_count} temporary files")


def validate_structure():
    """Validate project structure."""
    project_root = Path(__file__).parent.parent

    required_dirs = [
        "architecture",
        "benchmarks",
        "docs",
        "resources",
        "scripts",
        "tests",
        "translations",
        "UI",
        "utils",
    ]

    required_files = [
        "main_app.py",
        "config.json",
        "hardware.json",
        "readme.md",
        "TODO.md",
        ".gitignore",
    ]

    print("Validating project structure...")

    all_valid = True

    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            print(f"❌ Missing directory: {dir_name}")
            all_valid = False
        else:
            print(f"✅ Directory exists: {dir_name}")

    for file_name in required_files:
        file_path = project_root / file_name
        if not file_path.exists():
            print(f"❌ Missing file: {file_name}")
            all_valid = False
        else:
            print(f"✅ File exists: {file_name}")

    if all_valid:
        print("✅ Project structure is valid")
    else:
        print("❌ Project structure has issues")

    return all_valid


def main():
    """Main cleanup function."""
    print("🧹 CFAB UI Manager - Project Cleanup")
    print("=" * 40)

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "pycache":
            clean_pycache()
        elif command == "temp":
            clean_temp_files()
        elif command == "validate":
            validate_structure()
        elif command == "all":
            clean_pycache()
            clean_temp_files()
            validate_structure()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: pycache, temp, validate, all")
    else:
        # Default: clean everything
        clean_pycache()
        clean_temp_files()
        validate_structure()

    print("\n✅ Cleanup completed!")


if __name__ == "__main__":
    main()
