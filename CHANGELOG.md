# Changelog

All notable changes to CLI-agent-installer are documented in this file.

## [2.0.0] - 2026-05-03

### Added

#### Core System
- **ChecklistEngine** - Task-based installation with validation
  - Task and Step models with status tracking
  - Checkpoint system (save/load state)
  - Rollback on failure
  - Resume from checkpoint
  - Optional steps (don't fail checklist)
  - Retry mechanism with max_retries
  - Progress tracking (0-100%)
  - Duration tracking
  - Default task loading from manifest (7 tasks)

- **StructuredLogger** - Timestamped logging for audit trails
  - ISO 8601 timestamps
  - Structured fields (checklist_id, task_name, step_name, extra)
  - Log types: SYSTEM, TASK, STEP, ERROR, WARNING, CHECKPOINT, ROLLBACK
  - Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
  - JSON serialization
  - JSONL export (one JSON per line)
  - CSV export for spreadsheet compatibility
  - Per-checklist filtering
  - Console logging with color icons

#### CLI Interface
- **New commands:**
  - `installer tui <dir>` - Launch TUI interface
  - `installer serve` - Start REST API server
  - `installer checklist list <dir>` - List all checklists
  - `installer checklist run <dir>` - Run checklist
  - `installer checklist resume <dir> <id>` - Resume from checkpoint
  - `installer logs <dir>` - View/export logs with filters

- **Flags:**
  - `--verbose` - Enable verbose output
  - `--log-level` - Set log level (DEBUG, INFO, WARNING, ERROR)
  - `--dry-run` - Don't make changes
  - `--resume` - Resume from checkpoint ID
  - `--no-checklist` - Run without checklist system (legacy mode)

#### TUI Interface (Textual)
- **Screens:**
  - ChecklistScreen - Visual task/step management
  - LogScreen - Real-time log viewing
  - StatusScreen - Project status display

- **Widgets:**
  - TaskWidget - Display task with status icon
  - StepWidget - Display step with status icon
  - ListView - Task/step navigation
  - ProgressBar - Progress tracking
  - Log - Real-time log viewer
  - Button - Action buttons

- **Keybindings:**
  - `q` - Quit
  - `l` - Open log screen
  - `s` - Open status screen

- **Features:**
  - Real-time progress updates during checklist execution
  - Export logs from TUI (JSON/CSV)
  - Color-coded status indicators
  - Screen navigation (push/pop)

#### REST API (FastAPI)
- **Endpoints:**
  - `GET /health` - Health check
  - `POST /projects/{path}/checklists/run` - Run checklist (async)
  - `GET /projects/{path}/checklists` - List checklists
  - `GET /projects/{path}/checklists/{id}` - Get checklist details
  - `POST /projects/{path}/checklists/{id}/resume` - Resume checklist
  - `GET /projects/{path}/logs` - Get logs (filtered)
  - `GET /projects/{path}/logs/export` - Export logs (JSON/CSV)
  - `GET /projects/{path}/status` - Get project status
  - `WS /ws/checklists/{id}` - WebSocket for progress updates

- **Models:**
  - TaskModel, StepModel, LogEntryModel
  - ChecklistSummary, RunChecklistRequest
  - HealthResponse

- **Features:**
  - Async execution in background tasks
  - WebSocket for real-time progress updates
  - OpenAPI/Swagger auto-generated
  - Pydantic model validation
  - Error handling with HTTP status codes

#### Dependencies
- Add `textual>=0.80.0` for TUI interface
- Add `fastapi>=0.115.0` for REST API
- Add `uvicorn[standard]>=0.30.0` for ASGI server

### Changed
- Update version to 2.0.0
- Update package description to reflect new features
- Pydantic V2 compatibility across all modules
- Improve CLI output with color icons
- Enhance error handling

### Deprecated
- None

### Removed
- None

### Fixed
- Fix glob pattern matching in SyncManager (use rglob instead of glob with **)
- Fix Pydantic V2 deprecation warnings
- Fix test assertion for sync with no changes

### Security
- None

## [1.0.0] - 2026-05-03

### Added
- Initial release
- VersionManager (git tags, GitHub API)
- ManifestManager (Pydantic models)
- SyncManager (file sync with zombie removal)
- CLI interface (init, run, check, version)
- install.sh for self-installation
- README and ARCHITECTURE documentation

---

[2.0.0]: https://github.com/Ruben-Alvarez-Dev/CLI-agent-installer/releases/tag/v2.0.0
[1.0.0]: https://github.com/Ruben-Alvarez-Dev/CLI-agent-installer/releases/tag/v1.0.0
