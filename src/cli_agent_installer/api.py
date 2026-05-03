"""REST API for CLI-agent-installer using FastAPI.

Provides:
- Checklist management endpoints
- Log retrieval and export
- Health check
- Progress updates (WebSocket optional)
"""

from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from uvicorn import Config, Server

from . import (
    ChecklistEngine,
    StructuredLogger,
    ManifestManager,
    Task,
    Step,
    TaskStatus,
    LogEntry,
    LogType,
)


# ============ Pydantic Models ============


class TaskModel(BaseModel):
    """Task model for API."""

    name: str
    description: str
    status: str
    progress: float
    error: Optional[str] = None
    duration: Optional[float] = None
    timestamp_start: Optional[float] = None
    timestamp_end: Optional[float] = None


class StepModel(BaseModel):
    """Step model for API."""

    name: str
    description: str
    status: str
    error: Optional[str] = None
    duration: Optional[float] = None
    timestamp_start: Optional[float] = None
    timestamp_end: Optional[float] = None


class ChecklistSummary(BaseModel):
    """Checklist summary for API."""

    checklist_id: str
    timestamp: float
    task_name: str
    step_index: int
    completed_tasks: List[str] = Field(default_factory=list)


class LogEntryModel(BaseModel):
    """Log entry model for API."""

    timestamp: str
    level: str
    type: str
    message: str
    checklist_id: Optional[str] = None
    task_name: Optional[str] = None
    step_name: Optional[str] = None
    extra: dict = Field(default_factory=dict)
    duration: Optional[float] = None
    error_type: Optional[str] = None
    traceback: Optional[str] = None


class RunChecklistRequest(BaseModel):
    """Request to run checklist."""

    dry_run: bool = False
    verbose: bool = False


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    timestamp: str


# ============ FastAPI App ============

app = FastAPI(
    title="CLI-agent-installer API",
    description="REST API for managing installations with checklist system",
    version="2.0.0",
)

# Store active engines (for progress updates)
active_engines: dict[str, ChecklistEngine] = {}


# ============ Endpoints ============


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@app.post("/projects/{project_path:path}/checklists/run")
async def run_checklist(
    project_path: str,
    request: RunChecklistRequest,
    background_tasks: BackgroundTasks,
):
    """Run checklist for a project.

    Returns immediately and runs in background.
    """
    project_dir = Path(project_path).resolve()

    if not project_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_path}")

    # Initialize engine
    logger = StructuredLogger(project_dir)
    engine = ChecklistEngine(project_dir, logger)

    # Load manifest
    manifest_manager = ManifestManager(project_dir)
    manifest = manifest_manager.load()

    # Load tasks
    engine.load_tasks_from_manifest(manifest)

    # Store in active engines
    active_engines[engine.checklist_id] = engine

    # Run in background
    def run_in_background():
        engine.run(dry_run=request.dry_run)

    background_tasks.add_task(run_in_background)

    return {
        "status": "started",
        "checklist_id": engine.checklist_id,
        "dry_run": request.dry_run,
    }


@app.get("/projects/{project_path:path}/checklists")
async def list_checklists(project_path: str):
    """List all checklists for a project."""
    project_dir = Path(project_path).resolve()

    if not project_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_path}")

    logger = StructuredLogger(project_dir)
    engine = ChecklistEngine(project_dir, logger)

    checklists = engine.get_checklists()

    return {
        "project_path": str(project_dir),
        "checklists": checklists,
        "count": len(checklists),
    }


@app.get("/projects/{project_path:path}/checklists/{checklist_id}")
async def get_checklist(project_path: str, checklist_id: str):
    """Get checklist details by ID."""
    project_dir = Path(project_path).resolve()

    if not project_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_path}")

    logger = StructuredLogger(project_dir)
    engine = ChecklistEngine(project_dir, logger)

    checkpoint = engine._load_checkpoint(checklist_id)
    if not checkpoint:
        raise HTTPException(status_code=404, detail=f"Checkpoint not found: {checklist_id}")

    logs = logger.get_logs(checklist_id=checklist_id)

    return {
        "checklist_id": checklist_id,
        "checkpoint": checkpoint.to_dict(),
        "logs": [log.to_dict() for log in logs],
        "log_count": len(logs),
    }


@app.post("/projects/{project_path:path}/checklists/{checklist_id}/resume")
async def resume_checklist(
    project_path: str,
    checklist_id: str,
    background_tasks: BackgroundTasks,
):
    """Resume checklist from checkpoint."""
    project_dir = Path(project_path).resolve()

    if not project_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_path}")

    logger = StructuredLogger(project_dir)
    engine = ChecklistEngine(project_dir, logger)

    # Run in background
    def resume_in_background():
        engine.resume(checklist_id)

    background_tasks.add_task(resume_in_background)

    return {
        "status": "resumed",
        "checklist_id": checklist_id,
    }


@app.get("/projects/{project_path:path}/logs")
async def get_logs(
    project_path: str,
    checklist_id: Optional[str] = None,
    log_type: Optional[str] = None,
    level: Optional[str] = None,
):
    """Get logs for a project."""
    project_dir = Path(project_path).resolve()

    if not project_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_path}")

    logger = StructuredLogger(project_dir)

    # Parse filters
    log_type_filter = LogType(log_type) if log_type else None

    logs = logger.get_logs(
        checklist_id=checklist_id,
        log_type=log_type_filter,
        level=level,
    )

    return {
        "project_path": str(project_dir),
        "filters": {
            "checklist_id": checklist_id,
            "log_type": log_type,
            "level": level,
        },
        "logs": [log.to_dict() for log in logs],
        "count": len(logs),
    }


@app.get("/projects/{project_path:path}/logs/export")
async def export_logs(
    project_path: str,
    checklist_id: str,
    format: str = "json",
):
    """Export logs for a checklist."""
    project_dir = Path(project_path).resolve()

    if not project_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_path}")

    logger = StructuredLogger(project_dir)

    if format not in ["json", "csv"]:
        raise HTTPException(status_code=400, detail="format must be 'json' or 'csv'")

    filepath = logger.export_audit_trail(checklist_id, output_format=format)

    return FileResponse(
        path=filepath,
        filename=filepath.name,
        media_type="application/json" if format == "json" else "text/csv",
    )


@app.get("/projects/{project_path:path}/status")
async def get_project_status(project_path: str):
    """Get project installation status."""
    project_dir = Path(project_path).resolve()

    if not project_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_path}")

    logger = StructuredLogger(project_dir)
    engine = ChecklistEngine(project_dir, logger)

    # Get latest checkpoint
    latest_checkpoint = engine._find_latest_checkpoint()

    # Get recent logs
    recent_logs = logger.get_logs()[-10:] if logger.logs else []

    return {
        "project_path": str(project_dir),
        "has_installation": (project_dir / "install").exists(),
        "latest_checkpoint": latest_checkpoint.to_dict() if latest_checkpoint else None,
        "recent_logs": [log.to_dict() for log in recent_logs],
    }


# ============ WebSocket for Progress Updates ============


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, checklist_id: str, websocket: WebSocket):
        """Accept connection."""
        await websocket.accept()
        self.active_connections[checklist_id] = websocket

    def disconnect(self, checklist_id: str):
        """Remove connection."""
        if checklist_id in self.active_connections:
            del self.active_connections[checklist_id]

    async def send_progress(self, checklist_id: str, message: dict):
        """Send progress update."""
        if checklist_id in self.active_connections:
            await self.active_connections[checklist_id].send_json(message)


manager = ConnectionManager()


@app.websocket("/ws/checklists/{checklist_id}")
async def websocket_progress(websocket: WebSocket, checklist_id: str):
    """WebSocket endpoint for progress updates."""
    await manager.connect(checklist_id, websocket)

    try:
        # Keep connection alive
        while True:
            data = await websocket.receive_text()

            # Send progress update (placeholder)
            if checklist_id in active_engines:
                engine = active_engines[checklist_id]
                if engine.current_task:
                    task = engine.current_task
                    completed_steps = sum(1 for s in task.steps if s.status == TaskStatus.COMPLETED)
                    total_steps = len(task.steps)
                    progress = (completed_steps / total_steps * 100) if total_steps > 0 else 0

                    await manager.send_progress(
                        checklist_id,
                        {
                            "type": "progress",
                            "checklist_id": checklist_id,
                            "task_name": task.name,
                            "progress": progress,
                            "task_status": task.status.value,
                        },
                    )

    except WebSocketDisconnect:
        manager.disconnect(checklist_id)
