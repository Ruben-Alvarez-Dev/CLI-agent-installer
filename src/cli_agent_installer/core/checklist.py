"""Checklist Engine for CLI-agent-installer.

Provides:
- Task definition with validation
- Checklist with multiple tasks
- Execution engine with checkpoints
- Rollback on failure
- State persistence
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any

from .log import LogEntry, LogType, StructuredLogger
from .manifest import Manifest


class TaskStatus(Enum):
    """Status of a task execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Step:
    """A single step within a task."""

    name: str
    """Name of the step."""
    description: str
    """Human-readable description."""
    command: Optional[Callable] = None
    """Function to execute (optional if substeps exist)."""
    substeps: List["Step"] = field(default_factory=list)
    """Nested substeps."""
    status: TaskStatus = TaskStatus.PENDING
    """Current status."""
    error: Optional[str] = None
    """Error message if failed."""
    timestamp_start: Optional[float] = None
    """Start time (Unix timestamp)."""
    timestamp_end: Optional[float] = None
    """End time (Unix timestamp)."""
    required: bool = True
    """Whether this step is required (failure = fail task)."""
    retry_count: int = 0
    """Number of retries attempted."""
    max_retries: int = 0
    """Maximum retries allowed."""

    @property
    def duration(self) -> Optional[float]:
        """Calculate duration in seconds."""
        if self.timestamp_start and self.timestamp_end:
            return self.timestamp_end - self.timestamp_start
        return None


@dataclass
class Task:
    """A task with multiple steps."""

    name: str
    """Task identifier."""
    description: str
    """Human-readable description."""
    steps: List[Step] = field(default_factory=list)
    """Steps to execute."""
    status: TaskStatus = TaskStatus.PENDING
    """Current status."""
    progress: float = 0.0
    """Progress percentage (0-100)."""
    error: Optional[str] = None
    """Error message if failed."""
    timestamp_start: Optional[float] = None
    """Start time."""
    timestamp_end: Optional[float] = None
    """End time."""
    logs: List[LogEntry] = field(default_factory=list)
    """Logs generated during execution."""

    def add_step(self, step: Step) -> None:
        """Add a step to this task."""
        self.steps.append(step)

    def add_log(self, log: LogEntry) -> None:
        """Add a log entry."""
        self.logs.append(log)

    @property
    def duration(self) -> Optional[float]:
        """Calculate duration in seconds."""
        if self.timestamp_start and self.timestamp_end:
            return self.timestamp_end - self.timestamp_start
        return None


@dataclass
class Checkpoint:
    """Saved state of checklist execution."""

    checklist_id: str
    """Unique identifier for this checklist run."""
    timestamp: float
    """When checkpoint was saved."""
    task_name: str
    """Current task being executed."""
    step_index: int
    """Index of current step within task."""
    context: Dict[str, Any] = field(default_factory=dict)
    """Arbitrary context data."""
    completed_tasks: List[str] = field(default_factory=list)
    """List of completed task names."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "checklist_id": self.checklist_id,
            "timestamp": self.timestamp,
            "task_name": self.task_name,
            "step_index": self.step_index,
            "context": self.context,
            "completed_tasks": self.completed_tasks,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        """Deserialize from dict."""
        return cls(
            checklist_id=data["checklist_id"],
            timestamp=data["timestamp"],
            task_name=data["task_name"],
            step_index=data["step_index"],
            context=data.get("context", {}),
            completed_tasks=data.get("completed_tasks", []),
        )


class ChecklistEngine:
    """Engine for executing checklists with checkpoints."""

    def __init__(
        self,
        project_dir: Path,
        logger: Optional[StructuredLogger] = None,
        checkpoint_dir: Optional[Path] = None,
    ):
        """Initialize ChecklistEngine.

        Args:
            project_dir: Project directory
            logger: Structured logger (creates default if None)
            checkpoint_dir: Directory for checkpoint files
        """
        self.project_dir = Path(project_dir)
        self.logger = logger or StructuredLogger(project_dir)
        self.checkpoint_dir = checkpoint_dir or self.project_dir / ".checkpoints"

        self.checklist_id = f"{int(time.time())}"
        self.checkpoints: List[Checkpoint] = []
        self.tasks: List[Task] = []
        self.current_task: Optional[Task] = None

        # Ensure checkpoint dir exists
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def add_task(self, task: Task) -> None:
        """Add a task to the checklist."""
        self.tasks.append(task)

    def load_tasks_from_manifest(self, manifest: Manifest) -> None:
        """Create default tasks from manifest configuration.

        Args:
            manifest: Manifest object
        """
        # Task 1: Detection
        detect_task = Task(
            name="detection",
            description="Detect installation mode and system metadata",
        )
        detect_task.add_step(
            Step(name="detect_mode", description="Detect install/update/repair mode")
        )
        detect_task.add_step(
            Step(name="detect_system", description="Detect system metadata (Python, OS, etc.)")
        )
        self.add_task(detect_task)

        # Task 2: Backup (if update/repair)
        backup_task = Task(name="backup", description="Backup user data and config")
        backup_task.add_step(Step(name="backup_data", description="Backup data/ directory"))
        backup_task.add_step(Step(name="backup_config", description="Backup config/ directory"))
        backup_task.add_step(
            Step(name="backup_vault", description="Backup vault/ directory")
        )
        self.add_task(backup_task)

        # Task 3: Sync files
        sync_task = Task(name="sync", description="Synchronize project files")
        sync_task.add_step(
            Step(name="download_source", description="Download source from GitHub")
        )
        sync_task.add_step(
            Step(name="sync_files", description="Sync files with zombie removal")
        )
        sync_task.add_step(Step(name="verify_checksum", description="Verify file checksums"))
        self.add_task(sync_task)

        # Task 4: Dependencies
        deps_task = Task(name="dependencies", description="Install/update dependencies")
        deps_task.add_step(Step(name="create_venv", description="Create virtual environment"))
        deps_task.add_step(
            Step(name="install_deps", description="Install Python dependencies")
        )
        deps_task.add_step(Step(name="verify_deps", description="Verify critical dependencies"))
        self.add_task(deps_task)

        # Task 5: Configuration
        config_task = Task(name="configuration", description="Configure project")
        config_task.add_step(Step(name="generate_env", description="Generate .env file"))
        config_task.add_step(
            Step(name="generate_mcp_config", description="Generate MCP config"
        )
        )
        self.add_task(config_task)

        # Task 6: Services
        services_task = Task(name="services", description="Start/stop services")
        services_task.add_step(Step(name="stop_services", description="Stop running services"))
        services_task.add_step(Step(name="start_services", description="Start required services"))
        self.add_task(services_task)

        # Task 7: Verification
        verify_task = Task(name="verification", description="Verify installation")
        verify_task.add_step(Step(name="verify_files", description="Verify all files present"))
        verify_task.add_step(
            Step(name="verify_services", description="Verify services running")
        )
        verify_task.add_step(
            Step(name="verify_version", description="Verify version matches manifest"
        )
        self.add_task(verify_task)

    def run(
        self,
        dry_run: bool = False,
        resume_from_checkpoint: Optional[str] = None,
        on_progress: Optional[Callable[[Task, Step], None]] = None,
    ) -> bool:
        """Execute checklist.

        Args:
            dry_run: Don't make changes
            resume_from_checkpoint: ID of checkpoint to resume from
            on_progress: Callback for progress updates

        Returns:
            True if all tasks completed, False if any failed
        """
        self.logger.info(
            f"Starting checklist execution",
            extra={
                "checklist_id": self.checklist_id,
                "dry_run": dry_run,
                "task_count": len(self.tasks),
            },
        )

        # Load checkpoint if resuming
        start_task_index = 0
        if resume_from_checkpoint:
            checkpoint = self._load_checkpoint(resume_from_checkpoint)
            if checkpoint:
                start_task_index = self._find_task_index(checkpoint.task_name)
                self.logger.info(
                    f"Resuming from checkpoint",
                    extra={
                        "checkpoint_id": resume_from_checkpoint,
                        "task": checkpoint.task_name,
                        "step": checkpoint.step_index,
                    },
                )

        # Execute tasks
        for task_idx in range(start_task_index, len(self.tasks)):
            task = self.tasks[task_idx]

            # Skip if already completed
            if resume_from_checkpoint and task.name in self.checkpoints[0].completed_tasks:
                continue

            # Skip optional tasks if not applicable
            if task.name == "backup" and not self._should_backup():
                task.status = TaskStatus.SKIPPED
                self.logger.info(f"Skipping {task.name} task (not applicable)")
                continue

            self.current_task = task
            task.status = TaskStatus.RUNNING
            task.timestamp_start = time.time()

            self.logger.info(
                f"Starting task: {task.name}",
                extra={"task_name": task.name, "task_description": task.description},
            )

            # Execute steps
            task_success = True
            for step_idx, step in enumerate(task.steps):
                step.status = TaskStatus.RUNNING
                step.timestamp_start = time.time()

                self.logger.info(
                    f"Executing step: {step.name}",
                    extra={
                        "task_name": task.name,
                        "step_name": step.name,
                        "step_description": step.description,
                    },
                )

                if on_progress:
                    on_progress(task, step)

                try:
                    # Execute step
                    self._execute_step(step, dry_run)
                    step.status = TaskStatus.COMPLETED
                    step.timestamp_end = time.time()

                    # Save checkpoint after each step
                    self._save_checkpoint(task.name, step_idx)

                except Exception as e:
                    step.status = TaskStatus.FAILED
                    step.error = str(e)
                    step.timestamp_end = time.time()

                    self.logger.error(
                        f"Step failed: {step.name}",
                        extra={
                            "task_name": task.name,
                            "step_name": step.name,
                            "error": str(e),
                            "traceback": e.__traceback__.format_exc() if hasattr(e, "__traceback__") else None,
                        },
                    )

                    if step.required:
                        task.status = TaskStatus.FAILED
                        task.error = str(e)
                        task_success = False
                        break
                    else:
                        self.logger.warning(f"Optional step failed, continuing")
                        step.status = TaskStatus.SKIPPED

            task.timestamp_end = time.time()

            if task_success:
                task.status = TaskStatus.COMPLETED
                self.logger.info(
                    f"Task completed: {task.name}",
                    extra={"task_name": task.name, "duration": task.duration},
                )
            else:
                self.logger.error(
                    f"Task failed: {task.name}",
                    extra={"task_name": task.name, "error": task.error},
                )
                # Rollback
                self._rollback(task)

        all_success = all(t.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED] for t in self.tasks)

        self.logger.info(
            f"Checklist execution finished",
            extra={
                "checklist_id": self.checklist_id,
                "success": all_success,
                "dry_run": dry_run,
            },
        )

        return all_success

    def _execute_step(self, step: Step, dry_run: bool) -> None:
        """Execute a single step.

        Args:
            step: Step to execute
            dry_run: Don't make changes

        Raises:
            Exception: If step execution fails
        """
        # Execute substeps first
        if step.substeps:
            for substep in step.substeps:
                self._execute_step(substep, dry_run)
            return

        # Execute command
        if step.command:
            if dry_run:
                self.logger.info(
                    f"[DRY-RUN] Would execute: {step.name}",
                    extra={"step_name": step.name},
                )
            else:
                result = step.command()
                if not result:
                    raise Exception(f"Step {step.name} returned False")

    def _should_backup(self) -> bool:
        """Check if backup should be performed."""
        data_dir = self.project_dir / "data"
        config_dir = self.project_dir / "config"
        return data_dir.exists() or config_dir.exists()

    def _rollback(self, task: Task) -> None:
        """Rollback changes if task failed.

        Args:
            task: Task that failed
        """
        self.logger.warning(
            f"Rolling back task: {task.name}",
            extra={"task_name": task.name},
        )

        # Restore from latest checkpoint
        checkpoint = self._find_latest_checkpoint()
        if checkpoint:
            self._restore_checkpoint(checkpoint)
        else:
            self.logger.error("No checkpoint available for rollback")

    def _save_checkpoint(self, task_name: str, step_index: int) -> None:
        """Save checkpoint state.

        Args:
            task_name: Current task name
            step_index: Current step index
        """
        checkpoint = Checkpoint(
            checklist_id=self.checklist_id,
            timestamp=time.time(),
            task_name=task_name,
            step_index=step_index,
            completed_tasks=[t.name for t in self.tasks if t.status == TaskStatus.COMPLETED],
        )

        checkpoint_path = (
            self.checkpoint_dir / f"{self.checklist_id}_{task_name}.json"
        )
        with open(checkpoint_path, "w") as f:
            json.dump(checkpoint.to_dict(), f, indent=2)

        self.checkpoints.append(checkpoint)

    def _load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load checkpoint from file.

        Args:
            checkpoint_id: ID of checkpoint to load

        Returns:
            Checkpoint object or None
        """
        for file in self.checkpoint_dir.glob(f"{checkpoint_id}_*.json"):
            with open(file, "r") as f:
                data = json.load(f)
            return Checkpoint.from_dict(data)
        return None

    def _find_latest_checkpoint(self) -> Optional[Checkpoint]:
        """Find latest checkpoint.

        Returns:
            Latest checkpoint or None
        """
        checkpoints = []
        for file in self.checkpoint_dir.glob("*.json"):
            with open(file, "r") as f:
                data = json.load(f)
            checkpoint = Checkpoint.from_dict(data)
            checkpoints.append(checkpoint)

        if not checkpoints:
            return None

        return max(checkpoints, key=lambda c: c.timestamp)

    def _find_task_index(self, task_name: str) -> int:
        """Find index of task by name.

        Args:
            task_name: Task name to find

        Returns:
            Task index or 0 if not found
        """
        for i, task in enumerate(self.tasks):
            if task.name == task_name:
                return i
        return 0

    def _restore_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Restore state from checkpoint.

        Args:
            checkpoint: Checkpoint to restore
        """
        # Placeholder: implement actual restoration logic
        self.logger.info(
            f"Restoring from checkpoint",
            extra={
                "checkpoint_id": checkpoint.checklist_id,
                "task": checkpoint.task_name,
            },
        )

    def get_logs(self, checklist_id: Optional[str] = None) -> List[LogEntry]:
        """Get all logs for a checklist.

        Args:
            checklist_id: Filter by checklist ID (or all if None)

        Returns:
            List of log entries
        """
        if checklist_id:
            return [log for log in self.logger.logs if log.checklist_id == checklist_id]
        return self.logger.logs

    def get_checklists(self) -> List[Dict[str, Any]]:
        """Get all completed/in-progress checklists.

        Returns:
            List of checklist summaries
        """
        summaries = []
        for file in self.checkpoint_dir.glob("*.json"):
            with open(file, "r") as f:
                data = json.load(f)
            summaries.append(data)
        return summaries

    def resume(self, checklist_id: str) -> bool:
        """Resume a checklist from checkpoint.

        Args:
            checklist_id: ID of checklist to resume

        Returns:
            True if resumed successfully
        """
        return self.run(resume_from_checkpoint=checklist_id)
