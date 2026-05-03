# CLI-agent-installer

**Generic installer/updater for Python projects** with version management, update detection, and clean file synchronization.

## 🚀 Features

- ✅ **Single source of truth** for version (manifest.json → git tags)
- ✅ **Auto-detect updates** via GitHub releases API
- ✅ **Clean updates** with zombie file removal
- ✅ **Preserve user data** (data/, config/, .venv/ never touched)
- ✅ **Modular & reusable** — install once, use everywhere
- ✅ **Easy to adopt** — one command to initialize
- ✅ **Checklist system** for task-based installation with validation
- ✅ **Structured logging** with timestamps and audit trails (JSON/CSV export)
- ✅ **TUI interface** (Textual) for visual management
- ✅ **REST API** (FastAPI) with WebSocket for progress updates

## 📦 Installation

```bash
# From PyPI (recommended)
pip install CLI-agent-installer

# From source
git clone https://github.com/Ruben-Alvarez-Dev/CLI-agent-installer
cd CLI-agent-installer
pip install -e .
```

## 🎯 Usage

### 1. Initialize installer in a project

```bash
cd ~/my-project
CLI-agent-installer init . --repo "username/project-name"
```

This creates:
- `install/manifest.json` — Project configuration
- `install.sh` — Thin wrapper that calls `installer` CLI
- `install/update.sh` — Template orchestration script

### 2. Install/update project

```bash
CLI-agent-installer run ~/my-project
```

Performs:
1. Detect mode (install/update/repair)
2. Check for updates (if update mode)
3. Backup data (if exists)
4. Sync files (clean, with zombie removal)
5. Install dependencies
6. Verify installation

### 3. Check for updates

```bash
CLI-agent-installer check ~/my-project
```

Compares local version with latest GitHub release.

### 4. Print version

```bash
CLI-agent-installer version ~/my-project          # Show all versions
CLI-agent-installer version ~/my-project --git    # Show git tag version
CLI-agent-installer version ~/my-project --remote # Show latest GitHub release
```

## 📋 Manifest Configuration

`install/manifest.json` is the single source of truth:

```json
{
  "version": "1.0.0",
  "version_source": "git_tag",
  "repo": "owner/project-name",
  "python_min": "3.12",
  "payload": [
    "src/**",
    "tests/**",
    "pyproject.toml",
    "README.md"
  ],
  "preserve": [
    "data/**",
    "config/**",
    ".venv/**"
  ],
  "dependencies": [
    {"name": "pydantic", "import": "pydantic", "critical": true}
  ]
}
```

### Fields

| Field | Description |
|---|---|
| `version` | Current version |
| `version_source` | Source of version (`git_tag`, `manual`) |
| `repo` | GitHub repository (`owner/repo`) |
| `python_min` | Minimum Python version |
| `payload` | Globs for files to install |
| `preserve` | Globs for files to never delete |
| `dependencies` | Dependencies to verify |
| `services` | Services to manage (optional) |

## 🖥️ TUI Interface

Interactive terminal UI for visual project management.

```bash
CLI-agent-installer tui ~/my-project
```

**Keybindings:**
- `q` - Quit
- `l` - Open log screen
- `s` - Open status screen
- `Enter` - Run checklist

**Features:**
- Visual task/step progress display
- Real-time log viewer
- Export logs from TUI (JSON/CSV)
- Progress bar with percentage
- Color-coded status indicators

## 🌐 REST API

FastAPI-based REST API for remote management.

```bash
# Start server
CLI-agent-installer serve --host 0.0.0.0 --port 8000

# Or manually
uvicorn cli_agent_installer.api:app --reload
```

**Endpoints:**
- `GET /health` - Health check
- `POST /projects/{path}/checklists/run` - Run checklist (async)
- `GET /projects/{path}/checklists` - List checklists
- `GET /projects/{path}/checklists/{id}` - Get checklist details
- `POST /projects/{path}/checklists/{id}/resume` - Resume checklist
- `GET /projects/{path}/logs` - Get logs (filtered)
- `GET /projects/{path}/logs/export` - Export logs (JSON/CSV)
- `GET /projects/{path}/status` - Get project status
- `WS /ws/checklists/{id}` - WebSocket for progress updates

**Documentation:**
Open `http://localhost:8000/docs` for auto-generated OpenAPI/Swagger UI.

## 🔧 How It Works

### Thin Wrapper Pattern

`install.sh` is a thin wrapper (~20 lines) that calls the `installer` CLI:

```bash
#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="${1:-$HOME/my-project}"

if command -v installer &>/dev/null; then
    CLI-agent-installer run "$INSTALL_DIR"
else
    curl -fsSL https://raw.githubusercontent.com/.../install.sh | bash
    CLI-agent-installer run "$INSTALL_DIR"
fi
```

### Sync with Zombie Removal

The `SyncManager` ensures clean updates:

1. Collect files from source (payload patterns)
2. Collect files in destination
3. Detect zombies (files in dest but not in source)
4. Delete zombies (except files in preserve)
5. Copy new/modified files

Result: No stale files, no zombie modules.

## 📊 Comparison with Previous Approach

| Before (Copy-Paste) | After (CLI-agent-installer) |
|---|---|
| `install/` folder in each project | Single package installed system-wide |
| `install.sh` calls local scripts | `install.sh` calls `installer` CLI |
| Version management duplicated | Centralized in `installer` package |
| Not easily reusable | Universal — any Python project |
| Bug fixes require N updates | One fix → all projects benefit |

## 🔄 Migration from Current `install/`

For existing projects (e.g., MCP-agent-memory, CLI-agent-memory):

```bash
# 1. Install CLI-agent-installer
pip install CLI-agent-installer

# 2. Remove old install/ folder
rm -rf install/

# 3. Initialize new installer
CLI-agent-installer init . --repo "Ruben-Alvarez-Dev/your-project"

# 4. Commit changes
git add install.sh install/manifest.json
git commit -m "feat: switch to CLI-agent-installer"
```

**No data loss** — user data (`data/`, `config/`, etc.) is preserved.

## 🧪 Testing

```bash
# Dry-run mode (no changes)
CLI-agent-installer run ~/my-project --dry-run

# Test with custom source
CLI-agent-installer run ~/my-project --source ~/my-repo-checkout
```

## 📚 Examples

### Example 1: Simple Python project

```bash
cd ~/my-python-project
CLI-agent-installer init . --repo "myuser/myproject"
CLI-agent-installer run .
```

### Example 2: Check for updates in existing project

```bash
CLI-agent-installer check ~/my-existing-project
# Output: Local: 1.0.0 | Remote: v1.1.0
#         ⚠️  Update available
```

### Example 3: Force re-installation

```bash
# Delete and re-sync (preserves data)
CLI-agent-installer run ~/my-project
```

## 🛠️ Development

```bash
# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Format code
black src/
ruff check src/
```

## 📄 License

MIT

## 🤝 Contributing

Contributions welcome! Please read the [CONtribution Guide](CONTRIBUTING.md).

## 📞 Support

- GitHub Issues: https://github.com/Ruben-Alvarez-Dev/CLI-agent-installer/issues
- Documentation: https://github.com/Ruben-Alvarez-Dev/CLI-agent-installer

## 🌟 Acknowledgments

Built with:
- [Click](https://click.palletsprojects.com/) — CLI framework
- [Pydantic](https://docs.pydantic.dev/) — Data validation
- [Requests](https://requests.readthedocs.io/) — HTTP client
