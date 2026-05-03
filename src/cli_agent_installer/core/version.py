"""Version management for CLI-agent-installer.

Handles:
- Reading version from manifest.json
- Reading version from git tags
- Comparing local vs remote versions via GitHub API
- Bumping version in manifest.json
"""

import json
import subprocess
from pathlib import Path
from typing import Optional, Tuple
import requests


class VersionManager:
    """Manages version detection and comparison."""

    def __init__(self, project_dir: Path):
        """Initialize VersionManager.

        Args:
            project_dir: Path to the project directory containing manifest.json
        """
        self.project_dir = Path(project_dir)
        self.manifest_path = self.project_dir / "install" / "manifest.json"

    def get_local_version(self) -> str:
        """Get local version from manifest.json.

        Returns:
            Version string (e.g., "2.0.0") or "unknown" if not found
        """
        if not self.manifest_path.exists():
            return "unknown"

        try:
            with open(self.manifest_path, "r") as f:
                manifest = json.load(f)
            return manifest.get("version", "unknown")
        except (json.JSONDecodeError, IOError):
            return "unknown"

    def get_git_version(self) -> str:
        """Get version from git tags.

        Returns:
            Version string from git describe --tags (e.g., "v2.0.0-3-gae2331")
            or "no-git" if not a git repository
        """
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--always"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return "no-git"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return "no-git"

    def get_remote_version(self) -> Optional[str]:
        """Get latest version from GitHub releases API.

        Returns:
            Latest tag version (e.g., "v2.0.0") or None if unreachable
        """
        manifest = self._load_manifest()
        if not manifest:
            return None

        repo = manifest.get("repo")
        if not repo:
            return None

        url = f"https://api.github.com/repos/{repo}/releases/latest"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("tag_name")
            return None
        except requests.RequestException:
            return None

    def check_update_status(self) -> Tuple[str, str]:
        """Check if an update is available.

        Returns:
            Tuple of (status, remote_version)
            - status: "UP_TO_DATE", "UPDATE_AVAILABLE", or "UNKNOWN"
            - remote_version: Latest version from GitHub (or error message)
        """
        local = self.get_local_version()
        remote = self.get_remote_version()

        if not remote:
            return ("UNKNOWN", f"unreachable ({local})")

        # Remove 'v' prefix for comparison
        local_clean = local.lstrip("v")
        remote_clean = remote.lstrip("v")

        try:
            if local_clean == remote_clean:
                return ("UP_TO_DATE", remote)
            else:
                # Simple version comparison (not semantic version aware)
                return ("UPDATE_AVAILABLE", remote)
        except Exception:
            return ("UNKNOWN", remote)

    def bump_version(self, new_version: str) -> bool:
        """Bump version in manifest.json.

        Args:
            new_version: New version string (e.g., "2.1.0")

        Returns:
            True if successful, False otherwise
        """
        manifest = self._load_manifest()
        if not manifest:
            return False

        manifest["version"] = new_version

        try:
            self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)
            return True
        except IOError:
            return False

    def _load_manifest(self) -> Optional[dict]:
        """Load manifest.json.

        Returns:
            Manifest dict or None if not found/invalid
        """
        if not self.manifest_path.exists():
            return None

        try:
            with open(self.manifest_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
