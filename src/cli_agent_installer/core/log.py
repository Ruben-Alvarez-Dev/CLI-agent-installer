"""Structured logging for CLI-agent-installer.

Provides:
- Timestamped logs with ISO 8601 format
- Structured fields (dict-based logging)
- Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Serialization for audit trails
- Per-checklist filtering
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import traceback


class LogType(Enum):
    """Type of log entry."""

    SYSTEM = "system"
    TASK = "task"
    STEP = "step"
    ERROR = "error"
    WARNING = "warning"
    CHECKPOINT = "checkpoint"
    ROLLBACK = "rollback"


@dataclass
class LogEntry:
    """A single log entry with structured data."""

    timestamp: str
    """ISO 8601 timestamp."""
    level: str
    """Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""
    type: LogType
    """Type of log entry."""
    message: str
    """Human-readable message."""
    checklist_id: Optional[str] = None
    """Associated checklist ID."""
    task_name: Optional[str] = None
    """Associated task name."""
    step_name: Optional[str] = None
    """Associated step name."""
    extra: Dict[str, Any] = field(default_factory=dict)
    """Additional structured fields."""
    duration: Optional[float] = None
    """Duration in seconds (for performance logging)."""
    error_type: Optional[str] = None
    """Exception type if error."""
    traceback: Optional[str] = None
    """Full traceback if error."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for JSON."""
        data = {
            "timestamp": self.timestamp,
            "level": self.level,
            "type": self.type.value,
            "message": self.message,
        }

        # Add optional fields
        if self.checklist_id:
            data["checklist_id"] = self.checklist_id
        if self.task_name:
            data["task_name"] = self.task_name
        if self.step_name:
            data["step_name"] = self.step_name
        if self.extra:
            data["extra"] = self.extra
        if self.duration is not None:
            data["duration"] = self.duration
        if self.error_type:
            data["error_type"] = self.error_type
        if self.traceback:
            data["traceback"] = self.traceback

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogEntry":
        """Deserialize from dict."""
        return cls(
            timestamp=data["timestamp"],
            level=data["level"],
            type=LogType(data["type"]),
            message=data["message"],
            checklist_id=data.get("checklist_id"),
            task_name=data.get("task_name"),
            step_name=data.get("step_name"),
            extra=data.get("extra", {}),
            duration=data.get("duration"),
            error_type=data.get("error_type"),
            traceback=data.get("traceback"),
        )


class StructuredLogger:
    """Structured logger with serialization support."""

    def __init__(
        self,
        project_dir: Path,
        log_dir: Optional[Path] = None,
        console_level: int = logging.INFO,
    ):
        """Initialize StructuredLogger.

        Args:
            project_dir: Project directory
            log_dir: Directory for log files (default: .logs)
            console_level: Minimum log level for console output
        """
        self.project_dir = Path(project_dir)
        self.log_dir = log_dir or self.project_dir / ".logs"
        self.logs: List[LogEntry] = []

        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup console logger
        self.console_logger = logging.getLogger("installer")
        self.console_logger.setLevel(console_level)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        self.console_logger.addHandler(handler)

    def debug(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        checklist_id: Optional[str] = None,
        task_name: Optional[str] = None,
        step_name: Optional[str] = None,
    ) -> None:
        """Log debug message."""
        self._log(
            message=message,
            level="DEBUG",
            log_type=LogType.SYSTEM,
            extra=extra,
            checklist_id=checklist_id,
            task_name=task_name,
            step_name=step_name,
        )

    def info(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        checklist_id: Optional[str] = None,
        task_name: Optional[str] = None,
        step_name: Optional[str] = None,
    ) -> None:
        """Log info message."""
        self._log(
            message=message,
            level="INFO",
            log_type=LogType.SYSTEM,
            extra=extra,
            checklist_id=checklist_id,
            task_name=task_name,
            step_name=step_name,
        )

    def warning(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        checklist_id: Optional[str] = None,
        task_name: Optional[str] = None,
        step_name: Optional[str] = None,
    ) -> None:
        """Log warning message."""
        self._log(
            message=message,
            level="WARNING",
            log_type=LogType.WARNING,
            extra=extra,
            checklist_id=checklist_id,
            task_name=task_name,
            step_name=step_name,
        )

    def error(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        checklist_id: Optional[str] = None,
        task_name: Optional[str] = None,
        step_name: Optional[str] = None,
        exc: Optional[Exception] = None,
    ) -> None:
        """Log error message."""
        error_data = extra or {}
        if exc:
            error_data["error_type"] = type(exc).__name__
            error_data["traceback"] = traceback.format_exc()

        self._log(
            message=message,
            level="ERROR",
            log_type=LogType.ERROR,
            extra=error_data,
            checklist_id=checklist_id,
            task_name=task_name,
            step_name=step_name,
        )

    def log_task(
        self,
        task_name: str,
        status: str,
        description: str,
        extra: Optional[Dict[str, Any]] = None,
        checklist_id: Optional[str] = None,
    ) -> None:
        """Log task event."""
        message = f"Task {task_name}: {status}"
        task_extra = {"task_description": description, "task_status": status}
        if extra:
            task_extra.update(extra)

        self._log(
            message=message,
            level="INFO",
            log_type=LogType.TASK,
            extra=task_extra,
            checklist_id=checklist_id,
            task_name=task_name,
            step_name=None,  # Tasks don't have step_name
        )

    def log_step(
        self,
        step_name: str,
        status: str,
        description: str,
        extra: Optional[Dict[str, Any]] = None,
        checklist_id: Optional[str] = None,
        task_name: Optional[str] = None,
    ) -> None:
        """Log step event."""
        message = f"Step {step_name}: {status}"
        step_extra = {"step_description": description, "step_status": status}
        if extra:
            step_extra.update(extra)

        self._log(
            message=message,
            level="INFO",
            log_type=LogType.STEP,
            extra=step_extra,
            checklist_id=checklist_id,
            task_name=task_name,
            step_name=step_name,
        )

    def log_checkpoint(
        self,
        checkpoint_id: str,
        task_name: str,
        step_index: int,
        extra: Optional[Dict[str, Any]] = None,
        checklist_id: Optional[str] = None,
    ) -> None:
        """Log checkpoint event."""
        message = f"Checkpoint saved: {checkpoint_id}"
        checkpoint_extra = {
            "checkpoint_id": checkpoint_id,
            "task_name": task_name,
            "step_index": step_index,
        }
        if extra:
            checkpoint_extra.update(extra)

        self._log(
            message=message,
            level="INFO",
            log_type=LogType.CHECKPOINT,
            extra=checkpoint_extra,
            checklist_id=checklist_id,
        )

    def log_rollback(
        self,
        task_name: str,
        reason: str,
        extra: Optional[Dict[str, Any]] = None,
        checklist_id: Optional[str] = None,
    ) -> None:
        """Log rollback event."""
        message = f"Rollback task: {task_name} - {reason}"
        rollback_extra = {"task_name": task_name, "rollback_reason": reason}
        if extra:
            rollback_extra.update(extra)

        self._log(
            message=message,
            level="WARNING",
            log_type=LogType.ROLLBACK,
            extra=rollback_extra,
            checklist_id=checklist_id,
            task_name=task_name,
        )

    def _log(
        self,
        message: str,
        level: str,
        log_type: LogType,
        extra: Optional[Dict[str, Any]],
        checklist_id: Optional[str],
        task_name: Optional[str],
        step_name: Optional[str],
    ) -> None:
        """Internal logging method."""
        # Create log entry
        timestamp = datetime.utcnow().isoformat() + "Z"
        entry = LogEntry(
            timestamp=timestamp,
            level=level,
            type=log_type,
            message=message,
            checklist_id=checklist_id,
            task_name=task_name,
            step_name=step_name,
            extra=extra or {},
        )

        # Store in memory
        self.logs.append(entry)

        # Log to console
        if level == "DEBUG":
            self.console_logger.debug(message)
        elif level == "INFO":
            self.console_logger.info(message)
        elif level == "WARNING":
            self.console_logger.warning(message)
        elif level == "ERROR":
            self.console_logger.error(message)
        elif level == "CRITICAL":
            self.console_logger.critical(message)

    def save_to_file(self, checklist_id: str) -> Path:
        """Save logs to file.

        Args:
            checklist_id: ID of checklist

        Returns:
            Path to log file
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{checklist_id}_{timestamp}.jsonl"
        filepath = self.log_dir / filename

        # Filter logs for this checklist
        checklist_logs = [
            log for log in self.logs if log.checklist_id == checklist_id
        ]

        # Write as JSONL (one JSON per line)
        with open(filepath, "w") as f:
            for log in checklist_logs:
                f.write(json.dumps(log.to_dict()) + "\n")

        return filepath

    def load_from_file(self, filepath: Path) -> List[LogEntry]:
        """Load logs from file.

        Args:
            filepath: Path to log file

        Returns:
            List of log entries
        """
        logs = []
        with open(filepath, "r") as f:
            for line in f:
                data = json.loads(line)
                logs.append(LogEntry.from_dict(data))
        return logs

    def get_logs(
        self,
        checklist_id: Optional[str] = None,
        log_type: Optional[LogType] = None,
        level: Optional[str] = None,
    ) -> List[LogEntry]:
        """Get filtered logs.

        Args:
            checklist_id: Filter by checklist ID
            log_type: Filter by log type
            level: Filter by level

        Returns:
            Filtered list of log entries
        """
        filtered = self.logs

        if checklist_id:
            filtered = [log for log in filtered if log.checklist_id == checklist_id]

        if log_type:
            filtered = [log for log in filtered if log.type == log_type]

        if level:
            filtered = [log for log in filtered if log.level == level]

        return filtered

    def export_audit_trail(
        self,
        checklist_id: str,
        output_format: str = "json",
    ) -> Path:
        """Export audit trail for a checklist.

        Args:
            checklist_id: ID of checklist
            output_format: "json" or "csv"

        Returns:
            Path to exported file
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_{checklist_id}_{timestamp}.{output_format}"
        filepath = self.log_dir / filename

        checklist_logs = [
            log for log in self.logs if log.checklist_id == checklist_id
        ]

        if output_format == "json":
            with open(filepath, "w") as f:
                json.dump([log.to_dict() for log in checklist_logs], f, indent=2)

        elif output_format == "csv":
            import csv

            fields = [
                "timestamp",
                "level",
                "type",
                "message",
                "checklist_id",
                "task_name",
                "step_name",
            ]
            with open(filepath, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                for log in checklist_logs:
                    row = {field: getattr(log, field, "") for field in fields}
                    row["type"] = log.type.value
                    writer.writerow(row)

        return filepath
