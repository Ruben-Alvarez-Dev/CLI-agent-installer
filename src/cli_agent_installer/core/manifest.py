"""Manifest management for CLI-agent-installer.

Handles:
- Loading and validating manifest.json
- Providing typed access to manifest fields
- Template generation for new projects
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class Payload(BaseModel):
    """Payload configuration for files to install."""

    patterns: List[str] = Field(default_factory=list)
    """Glob patterns for files/directories to include in sync."""


class Preserve(BaseModel):
    """Preserve configuration for files to never delete."""

    patterns: List[str] = Field(default_factory=list)
    """Glob patterns for files/directories to exclude from deletion."""


class Dependency(BaseModel):
    """Dependency configuration for verification."""

    name: str
    """Package name (e.g., "mcp")"""
    import_: str = Field(alias="import")
    """Python import name (e.g., "mcp")"""
    critical: bool = False
    """Whether this dependency is critical (fail if missing)"""

    model_config = {
        "validate_by_name": True,
        "populate_by_name": True,
    }


class ServiceConfig(BaseModel):
    """Service configuration (e.g., Qdrant, llama-server)."""

    port: int
    """Port number for the service."""
    required: bool = False
    """Whether this service is required."""


class Services(BaseModel):
    """Services configuration."""

    qdrant: Optional[ServiceConfig] = None
    """Qdrant vector database configuration."""
    llama_server: Optional[ServiceConfig] = None
    """Llama.cpp server configuration."""


class Manifest(BaseModel):
    """Manifest configuration for a project.

    This is the single source of truth for:
    - Version information
    - Files to install (payload)
    - Files to preserve (user data)
    - Dependencies to verify
    - Services to manage
    """

    version: str
    """Current version of the project."""

    version_source: str = "git_tag"
    """Source of version information ("git_tag", "manual", etc.)."""

    repo: str
    """GitHub repository name in "owner/repo" format."""

    python_min: str = "3.12"
    """Minimum Python version required."""

    payload: List[str] = Field(default_factory=list)
    """Glob patterns for files to install/update."""

    preserve: List[str] = Field(default_factory=list)
    """Glob patterns for files to preserve (never delete)."""

    dependencies: List[Dependency] = Field(default_factory=list)
    """Dependencies to verify during installation."""

    services: Services = Field(default_factory=Services)
    """Services to manage."""

    @field_validator("version_source")
    @classmethod
    def validate_version_source(cls, v):
        """Validate version_source field."""
        allowed = ["git_tag", "manual", "auto"]
        if v not in allowed:
            raise ValueError(f"version_source must be one of {allowed}")
        return v

    @field_validator("repo")
    @classmethod
    def validate_repo(cls, v):
        """Validate repo format."""
        if "/" not in v:
            raise ValueError('repo must be in "owner/repo" format')
        return v


class ManifestManager:
    """Manages manifest.json operations."""

    def __init__(self, project_dir: Path):
        """Initialize ManifestManager.

        Args:
            project_dir: Path to the project directory
        """
        self.project_dir = Path(project_dir)
        self.manifest_path = self.project_dir / "install" / "manifest.json"

    def load(self) -> Optional[Manifest]:
        """Load manifest.json.

        Returns:
            Manifest object or None if not found/invalid
        """
        if not self.manifest_path.exists():
            return None

        try:
            with open(self.manifest_path, "r") as f:
                data = json.load(f)
            return Manifest(**data)
        except (json.JSONDecodeError, IOError, ValueError) as e:
            return None

    def save(self, manifest: Manifest) -> bool:
        """Save manifest.json.

        Args:
            manifest: Manifest object to save

        Returns:
            True if successful, False otherwise
        """
        try:
            self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.manifest_path, "w") as f:
                json.dump(manifest.model_dump(by_alias=True), f, indent=2)
            return True
        except IOError:
            return False

    def generate_template(
        self,
        repo: str,
        version: str = "1.0.0",
        python_min: str = "3.12",
    ) -> Manifest:
        """Generate a template manifest for a new project.

        Args:
            repo: GitHub repository (owner/repo)
            version: Initial version
            python_min: Minimum Python version

        Returns:
            Manifest object with sensible defaults
        """
        return Manifest(
            version=version,
            repo=repo,
            python_min=python_min,
            payload=[
                "src/**",
                "tests/**",
                "pyproject.toml",
                "README.md",
                "install/**",
            ],
            preserve=[
                "data/**",
                "config/**",
                ".venv/**",
                "models/**",
                "backups/**",
            ],
            dependencies=[
                Dependency(name="pydantic", import_="pydantic", critical=True),
            ],
        )
