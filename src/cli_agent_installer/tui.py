"""TUI interface for CLI-agent-installer using Charm Textual.

Provides:
- Visual checklist management
- Real-time log viewer
- Progress bar and status display
- Interactive navigation
- Keyboard shortcuts
- Crush-inspired theme
"""

from pathlib import Path
from typing import List, Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header,
    Footer,
    Static,
    ListView,
    ListItem,
    Label,
    Button,
    ProgressBar,
    Log,
    DataTable,
)
from textual.reactive import reactive
from textual import events
from textual.screen import Screen

from .core import (
    ChecklistEngine,
    StructuredLogger,
    ManifestManager,
    Task,
    Step,
    TaskStatus,
    LogEntry,
    LogType,
)


# ============ Widgets ============


class TaskWidget(ListItem):
    """Widget for displaying a task."""

    def __init__(self, task: Task):
        """Initialize task widget.

        Args:
            task: Task to display
        """
        self.task = task
        status_icon = {
            TaskStatus.PENDING: "○",
            TaskStatus.RUNNING: "●",
            TaskStatus.COMPLETED: "✓",
            TaskStatus.FAILED: "✗",
            TaskStatus.SKIPPED: "−",
        }.get(task.status, "?")

        super().__init__(
            Static(f"{status_icon} {task.name} ({int(task.progress)}%)"),
        )


class StepWidget(ListItem):
    """Widget for displaying a step."""

    def __init__(self, step: Step):
        """Initialize step widget.

        Args:
            step: Step to display
        """
        self.step = step
        status_icon = {
            TaskStatus.PENDING: "○",
            TaskStatus.RUNNING: "●",
            TaskStatus.COMPLETED: "✓",
            TaskStatus.FAILED: "✗",
            TaskStatus.SKIPPED: "−",
        }.get(step.status, "?")

        super().__init__(
            Static(f"  {status_icon} {step.name} - {step.description}"),
        )


# ============ Screens ============


class ChecklistScreen(Screen):
    """Screen for checklist management."""

    def __init__(self, project_dir: Path):
        """Initialize checklist screen.

        Args:
            project_dir: Project directory
        """
        super().__init__()
        self.project_dir = project_dir
        self.logger = StructuredLogger(project_dir)
        self.engine = ChecklistEngine(project_dir, self.logger)

        # Load tasks
        manifest_manager = ManifestManager(project_dir)
        manifest = manifest_manager.load()
        self.engine.load_tasks_from_manifest(manifest)

    def compose(self) -> ComposeResult:
        """Compose screen UI."""
        yield Header()
        yield Container(
            Vertical(
                Label(f"Checklist: {self.project_dir.name}", classes="title"),
                ListView(id="task_list"),
                ProgressBar(id="progress_bar", show_eta=False),
                Button("Run Checklist", id="btn_run", variant="primary"),
                Button("Exit", id="btn_exit"),
                classes="content",
            ),
        )
        yield Footer()

    def on_mount(self) -> None:
        """Mount screen."""
        self._update_task_list()

    def _update_task_list(self) -> None:
        """Update task list widget."""
        task_list = self.query_one("#task_list", ListView)
        task_list.clear()

        for task in self.engine.tasks:
            task_list.append(TaskWidget(task))

        # Update progress bar
        total_progress = sum(t.progress for t in self.engine.tasks) / len(self.engine.tasks)
        self.query_one("#progress_bar", ProgressBar).advance(total_progress)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press.

        Args:
            event: Button press event
        """
        if event.button.id == "btn_run":
            self._run_checklist()
        elif event.button.id == "btn_exit":
            self.app.exit()

    def _run_checklist(self) -> None:
        """Run checklist."""
        def on_progress(task: Task, step: Step):
            """Update UI on progress."""
            self._update_task_list()

        success = self.engine.run(on_progress=on_progress)

        if success:
            self.app.notify("Checklist completed!", severity="success")
        else:
            self.app.notify("Checklist failed!", severity="error")


class LogScreen(Screen):
    """Screen for log viewing."""

    def __init__(self, project_dir: Path, checklist_id: Optional[str] = None):
        """Initialize log screen.

        Args:
            project_dir: Project directory
            checklist_id: Filter by checklist ID
        """
        super().__init__()
        self.project_dir = project_dir
        self.checklist_id = checklist_id
        self.logger = StructuredLogger(project_dir)

    def compose(self) -> ComposeResult:
        """Compose screen UI."""
        yield Header()
        yield Container(
            Vertical(
                Label(f"Logs: {self.project_dir.name}", classes="title"),
                Log(id="log_widget"),
                Button("Back", id="btn_back"),
                Button("Export JSON", id="btn_export_json"),
                Button("Export CSV", id="btn_export_csv"),
                classes="content",
            ),
        )
        yield Footer()

    def on_mount(self) -> None:
        """Mount screen."""
        self._load_logs()

    def _load_logs(self) -> None:
        """Load logs into widget."""
        log_widget = self.query_one("#log_widget", Log)
        logs = self.logger.get_logs(checklist_id=self.checklist_id)

        for log in logs:
            level_icon = {
                "DEBUG": "🔍",
                "INFO": "ℹ️",
                "WARNING": "⚠️",
                "ERROR": "❌",
                "CRITICAL": "🚨",
            }.get(log.level, "•")

            log_widget.write_line(
                f"[{log.timestamp}] [{level_icon}] {log.type.value}: {log.message}"
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press.

        Args:
            event: Button press event
        """
        if event.button.id == "btn_back":
            self.app.pop_screen()
        elif event.button.id == "btn_export_json":
            self._export_logs("json")
        elif event.button.id == "btn_export_csv":
            self._export_logs("csv")

    def _export_logs(self, format: str) -> None:
        """Export logs.

        Args:
            format: Export format (json/csv)
        """
        if self.checklist_id:
            filepath = self.logger.export_audit_trail(self.checklist_id, format)
        else:
            self.app.notify("No checklist ID specified!", severity="error")
            return

        self.app.notify(f"Logs exported to {filepath}", severity="success")


class StatusScreen(Screen):
    """Screen for project status."""

    def __init__(self, project_dir: Path):
        """Initialize status screen.

        Args:
            project_dir: Project directory
        """
        super().__init__()
        self.project_dir = project_dir
        self.logger = StructuredLogger(project_dir)
        self.engine = ChecklistEngine(project_dir, self.logger)

    def compose(self) -> ComposeResult:
        """Compose screen UI."""
        yield Header()
        yield Container(
            Vertical(
                Label(f"Status: {self.project_dir.name}", classes="title"),
                Static(id="status_info"),
                DataTable(id="log_table"),
                Button("Back", id="btn_back"),
                classes="content",
            ),
        )
        yield Footer()

    def on_mount(self) -> None:
        """Mount screen."""
        self._load_status()

    def _load_status(self) -> None:
        """Load status into widget."""
        status_info = self.query_one("#status_info", Static)
        log_table = self.query_one("#log_table", DataTable)

        # Display status
        has_installation = (self.project_dir / "install").exists()
        status_info.update(
            f"Has installation: {has_installation}\n"
            f"Logs directory: {self.logger.log_dir}\n"
            f"Checkpoint directory: {self.engine.checkpoint_dir}"
        )

        # Setup table
        log_table.add_column("Timestamp")
        log_table.add_column("Level")
        log_table.add_column("Type")
        log_table.add_column("Message")

        # Add recent logs
        recent_logs = self.logger.get_logs()[-10:] if self.logger.logs else []
        for log in recent_logs:
            log_table.add_row(
                log.timestamp,
                log.level,
                log.type.value,
                log.message[:50] + "..." if len(log.message) > 50 else log.message,
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press.

        Args:
            event: Button press event
        """
        if event.button.id == "btn_back":
            self.app.pop_screen()


# ============ Main App ============


class InstallerTUI(App):
    """Main TUI application for CLI-agent-installer."""

    CSS = """
    Screen {
        layout: vertical;
    }

    Container {
        padding: 1;
    }

    .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    .content {
        height: 100%;
    }

    ListView {
        height: 1fr;
    }

    Log {
        height: 1fr;
        border: solid $primary;
    }

    Button {
        margin: 1 1 0 0;
    }

    #progress_bar {
        margin: 1 0;
    }

    Static {
        padding: 1 0;
    }
    """

    TITLE = "CLI-agent-installer v2.0"

    def __init__(self, project_dir: Optional[Path] = None):
        """Initialize TUI app.

        Args:
            project_dir: Project directory to manage
        """
        super().__init__()
        self.project_dir = project_dir

    def on_mount(self) -> None:
        """Mount app."""
        if self.project_dir:
            self.push_screen(ChecklistScreen(self.project_dir))

    def action_open_logs(self) -> None:
        """Open log screen."""
        if self.project_dir:
            self.push_screen(LogScreen(self.project_dir))

    def action_open_status(self) -> None:
        """Open status screen."""
        if self.project_dir:
            self.push_screen(StatusScreen(self.project_dir))

    def action_quit(self) -> None:
        """Quit application."""
        self.exit()


def run_tui(project_dir: Optional[Path] = None) -> None:
    """Run TUI application.

    Args:
        project_dir: Project directory to manage
    """
    app = InstallerTUI(project_dir)
    app.run()


if __name__ == "__main__":
    run_tui()
