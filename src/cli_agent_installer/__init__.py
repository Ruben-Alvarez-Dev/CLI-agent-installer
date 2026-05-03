"""CLI-agent-installer — Generic installer/updater for Python projects.

This package provides a unified way to install, update, and manage
Python projects with automatic version detection, GitHub API integration,
clean file synchronization, checklist-based installation, structured logging,
and multiple interfaces (CLI, TUI, REST API).

Usage:
    installer init ~/my-project       # Initialize installer in a project
    installer run ~/my-project        # Install/update project
    installer check ~/my-project      # Check for updates
    installer version ~/my-project    # Print version
    installer tui ~/my-project        # Launch TUI interface
    installer serve                   # Start REST API server
"""

__version__ = "2.0.0"

from .core.version import VersionManager
from .core.manifest import ManifestManager
from .core.sync import SyncManager
from .core.checklist import (
    ChecklistEngine,
    Task,
    Step,
    TaskStatus,
    Checkpoint,
)
from .core.log import (
    StructuredLogger,
    LogEntry,
    LogType,
)

__all__ = [
    "VersionManager",
    "ManifestManager",
    "SyncManager",
    "ChecklistEngine",
    "StructuredLogger",
    "LogEntry",
    "LogType",
    "Task",
    "Step",
    "TaskStatus",
    "Checkpoint",
]
