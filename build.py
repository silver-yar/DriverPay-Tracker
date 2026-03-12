#!/usr/bin/env python3
"""
Cross-platform build script for DriverPay-Tracker
Packages the application for Windows, macOS, and Linux using PyInstaller
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Configuration
APP_NAME = "DriverPay-Tracker"
APP_VERSION = "1.0.0"
MAIN_SCRIPT = "src/main.py"
DIST_DIR = "dist"
BUILD_DIR = "build"

# Directories to include from src
ADDITIONAL_DIRS = [
    ("src/ui", "ui"),
    ("src/db", "db"),
]


def get_base_options():
    """Get base PyInstaller options"""
    return [
        "--name=" + APP_NAME,
        "--windowed",  # No console window
        "--onefile",  # Single executable
        "--clean",  # Clean build cache
        "--noconfirm",  # Don't ask for confirmation
    ]


def get_platform_specific_options():
    """Get platform-specific PyInstaller options"""
    system = platform.system()

    if system == "Windows":
        return [
            "--icon=assets/icon.ico" if Path("assets/icon.ico").exists() else "",
            "--add-data=src/ui;ui",
            "--add-data=src/db;db",
            "--hidden-import=PySide6",
            "--hidden-import=PySide6.QtCore",
            "--hidden-import=PySide6.QtWidgets",
            "--hidden-import=PySide6.QtWebEngineWidgets",
            "--hidden-import=PySide6.QtWebChannel",
            "--hidden-import=PySide6.QtWebEngineCore",
            "--collect-all=PySide6",
            "--collect-all=webengineelements",
        ]
    elif system == "Darwin":  # macOS
        return [
            "--icon=assets/icon.icns" if Path("assets/icon.icns").exists() else "",
            "--osx-bundle-identifier=com.driverpay.tracker",
            "--add-data=src/ui:ui",
            "--add-data=src/db:db",
            "--hidden-import=PySide6",
            "--hidden-import=PySide6.QtCore",
            "--hidden-import=PySide6.QtWidgets",
            "--hidden-import=PySide6.QtWebEngineWidgets",
            "--hidden-import=PySide6.QtWebChannel",
            "--hidden-import=PySide6.QtWebEngineCore",
            "--collect-all=PySide6",
            "--collect-all=webengineelements",
        ]
    else:  # Linux
        return [
            "--add-data=src/ui:ui",
            "--add-data=src/db:db",
            "--hidden-import=PySide6",
            "--hidden-import=PySide6.QtCore",
            "--hidden-import=PySide6.QtWidgets",
            "--hidden-import=PySide6.QtWebEngineWidgets",
            "--hidden-import=PySide6.QtWebChannel",
            "--hidden-import=PySide6.QtWebEngineCore",
            "--collect-all=PySide6",
            "--collect-all=webengineelements",
        ]


def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import PyInstaller

        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def build_application():
    """Build the application using PyInstaller"""
    print(f"\n{'=' * 50}")
    print(f"Building {APP_NAME} for {platform.system()}")
    print(f"{'=' * 50}\n")

    # Clean previous builds
    if Path(DIST_DIR).exists():
        shutil.rmtree(DIST_DIR)
    if Path(BUILD_DIR).exists():
        shutil.rmtree(BUILD_DIR)

    # Build command
    cmd = (
        [
            sys.executable,
            "-m",
            "PyInstaller",
        ]
        + get_base_options()
        + get_platform_specific_options()
        + [MAIN_SCRIPT]
    )

    # Filter out empty strings
    cmd = [c for c in cmd if c]

    print("Running PyInstaller command:")
    print(" ".join(cmd) + "\n")

    subprocess.check_call(cmd)

    # Note: Database is created on first launch, not copied during build

    print(f"\n{'=' * 50}")
    print(f"Build complete!")
    print(f"Executable location: {DIST_DIR}/{APP_NAME}")
    print(f"{'=' * 50}\n")


def create_installer_windows():
    """Create Windows installer using Inno Setup or NSIS"""
    print("Creating Windows installer...")

    # Check for NSIS
    try:
        subprocess.check_call(
            ["makensis", "/VERSION"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        nsis_script = """
; DriverPay-Tracker NSIS Installer Script
!include "MUI2.nsh"

Name "DriverPay-Tracker"
OutFile "DriverPay-Tracker-Setup.exe"
InstallDir "$PROGRAMFILES\\DriverPay-Tracker"

Section "Install"
    SetOutPath "$INSTDIR"
    File "dist\\DriverPay-Tracker.exe"
    CreateShortcut "$DESKTOP\\DriverPay-Tracker.lnk" "$INSTDIR\\DriverPay-Tracker.exe"
SectionEnd
"""
        with open("installer.nsi", "w") as f:
            f.write(nsis_script)

        subprocess.check_call(["makensis", "installer.nsi"])
        print("Windows installer created: DriverPay-Tracker-Setup.exe")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("NSIS not found. Skipping installer creation.")
        print("You can create an installer manually using:")
        print("  - Inno Setup: https://jrsoftware.org/isinfo.php")
        print("  - NSIS: https://nsis.sourceforge.io/")


def create_dmg_macos():
    """Create macOS DMG"""
    print("Creating macOS DMG...")

    app_path = f"dist/{APP_NAME}.app"
    dmg_path = f"dist/{APP_NAME}-{APP_VERSION}.dmg"

    if not Path(app_path).exists():
        print(f"App bundle not found at {app_path}")
        return

    try:
        # Use create-dmg if available
        subprocess.check_call(
            [
                "create-dmg",
                "--volname",
                APP_NAME,
                "--window-pos",
                "200",
                "120",
                "--size",
                "200",
                "--icon",
                app_path,
                "150",
                "120",
                dmg_path,
                app_path,
            ]
        )
        print(f"DMG created: {dmg_path}")
    except FileNotFoundError:
        print("create-dmg not found. Creating DMG manually...")
        subprocess.check_call(
            [
                "hdiutil",
                "create",
                "-volname",
                APP_NAME,
                "-srcfolder",
                app_path,
                "-ov",
                "-format",
                "UDZO",
                dmg_path,
            ]
        )
        print(f"DMG created: {dmg_path}")


def create_appimage_linux():
    """Create Linux AppImage"""
    print("Creating Linux AppImage...")

    try:
        subprocess.check_call(["python3", "-m", "pip", "install", "appimage-builder"])

        # Create AppImage config
        config = f"""appimage-builder.yml
AppImage.name: {APP_NAME}
AppImage.version: {APP_VERSION}
AppImage.runtime:
  path: runtime
  version: '23.08'
AppImage.appimage:
  arch: x86_64
  update-information: none
AppImage.script: |
  # Add runtime dependencies here
"""
        with open("appimage-builder.yml", "w") as f:
            f.write(config)

        subprocess.check_call(["appimage-builder", "--generate"])
        print("AppImage configuration generated. Run: appimage-builder")
    except FileNotFoundError:
        print("appimage-builder not found.")
        print("Install it with: pip install appimage-builder")


def main():
    """Main build function"""
    print(f"Building {APP_NAME} v{APP_VERSION}")
    print(f"Platform: {platform.system()} ({platform.machine()})")
    print(f"Python: {sys.version}")

    # Check dependencies
    check_dependencies()

    # Build the application
    build_application()

    # Create platform-specific installers
    system = platform.system()

    if system == "Windows":
        create_installer_windows()
    elif system == "Darwin":
        create_dmg_macos()
    elif system == "Linux":
        create_appimage_linux()

    print("\nBuild process complete!")
    print(f"Output directory: {DIST_DIR}")


if __name__ == "__main__":
    main()
