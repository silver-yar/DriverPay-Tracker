#!/usr/bin/env python3
"""
Cleanup script for DriverPay-Tracker build artifacts
Removes build, dist, and other generated files
"""

import shutil
import sys
from pathlib import Path

# Directories and files to remove
CLEANUP_TARGETS = [
    "build",
    "dist",
    "__pycache__",
    ".pytest_cache",
]

# Specific files to remove
CLEANUP_FILES = [
    "DriverPay-Tracker.spec",
    "DriverPay-Tracker.spec.old",
    "installer.nsi",
    "appimage-builder.yml",
]


def cleanup():
    """Remove build artifacts and temporary files."""
    project_root = Path(__file__).parent

    removed_count = 0

    # Remove directories
    for target in CLEANUP_TARGETS:
        path = project_root / target
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
                print(f"Removed directory: {target}/")
            else:
                path.unlink()
                print(f"Removed file: {target}")
            removed_count += 1

    # Remove specific files
    for target in CLEANUP_FILES:
        path = project_root / target
        if path.exists():
            path.unlink()
            print(f"Removed file: {target}")
            removed_count += 1

    # Remove .pyc files recursively
    for pyc_file in project_root.rglob("*.pyc"):
        pyc_file.unlink()
        print(f"Removed: {pyc_file.relative_to(project_root)}")
        removed_count += 1

    # Remove __pycache__ directories that might remain
    for pycache_dir in project_root.rglob("__pycache__"):
        shutil.rmtree(pycache_dir)
        print(f"Removed: {pycache_dir.relative_to(project_root)}/")
        removed_count += 1

    if removed_count == 0:
        print("No cleanup needed - no build artifacts found.")
    else:
        print(f"\nCleanup complete! Removed {removed_count} item(s).")


if __name__ == "__main__":
    print("Cleaning up build artifacts...\n")
    cleanup()
