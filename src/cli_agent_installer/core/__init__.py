"""Core modules for CLI-agent-installer."""

from .version import VersionManager
from .manifest import ManifestManager, Manifest, Dependency, ServiceConfig
from .sync import SyncManager
from .checklist import (
    ChecklistEngine,
    Task,
    Step,
    TaskStatus,
    Checkpoint,
)
from .log import (
    StructuredLogger,
    LogEntry,
    LogType,
)

__all__ = [
    # Version management
    "VersionManager",
    # Manifest
    "ManifestManager",
    "Manifest",
    "Dependency",
    "ServiceConfig",
    # Sync
    "SyncManager",
    # Checklist
    "ChecklistEngine",
    "Task",
    "Step",
    "TaskStatus",
    "Checkpoint",
    # Logging
    "StructuredLogger",
    "LogEntry",
    "LogType",
]
