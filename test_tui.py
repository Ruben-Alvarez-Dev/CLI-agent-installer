#!/usr/bin/env python3
"""Test TUI with a simple mock project."""

import tempfile
from pathlib import Path

# Create a temporary test project
test_dir = Path(tempfile.mkdtemp(prefix="test-tui-"))

# Create manifest.json
manifest = {
    "version": "1.0.0",
    "version_source": "manual",
    "repo": "test/test-project",
    "python_min": "3.12",
    "payload": ["*.md"],
    "preserve": ["data/**"],
    "dependencies": [],
}

manifest_path = test_dir / "install" / "manifest.json"
manifest_path.parent.mkdir(parents=True, exist_ok=True)
manifest_path.write_text(manifest.__repr__().replace("'", '"'))

# Create a README
readme_path = test_dir / "README.md"
readme_path.write_text("# Test Project\n\nThis is a test project for TUI testing.\n")

# Create a data directory
data_dir = test_dir / "data"
data_dir.mkdir(parents=True, exist_ok=True)

print(f"Test project created at: {test_dir}")
print(f"Manifest: {manifest_path}")
print(f"README: {readme_path}")
print(f"Data: {data_dir}")

# Try to import and run TUI
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

    from cli_agent_installer.tui import run_tui

    print("\nLaunching TUI...")
    run_tui(test_dir)

except Exception as e:
    print(f"Error running TUI: {e}")
    import traceback
    traceback.print_exc()
