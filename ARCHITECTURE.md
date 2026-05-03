# CLI-agent-installer — Generic Installer Architecture

## Problem Statement

The current `install/` directory exists as **copied code** in two projects (MCP and CLI). This is **not abstraction**. We need a **standalone installer** that any project can use.

## Solution Design

### Repository Structure

```
CLI-agent-installer/
├── pyproject.toml              ← Python package (pip install CLI-agent-installer)
├── README.md                   ← Usage examples
├── src/
│   └── cli_agent_installer/
│       ├── __init__.py         ← Package entry point
│       ├── cli.py              ← CLI: installer run <project-path>
│       ├── core/               ← Core logic (project-agnostic)
│       │   ├── __init__.py
│       │   ├── version.py      ← Read version, GitHub API check
│       │   ├── sync.py         ← Clean sync with zombie removal
│       │   ├── backup.py       ← Backup user data
│       │   ├── manifest.py     ← Load/validate manifest.json
│       │   ├── deps.py         ← Dependency installation
│       │   └── services.py     ← Service management (optional)
│       └── templates/          ← Template files to inject into projects
│           ├── manifest.json    ← Template manifest
│           ├── install.sh       ← Template thin wrapper
│           ├── install/update.sh ← Template orchestrator
│           └── install/        ← Template modular scripts
│               ├── detect.sh
│               ├── backup.sh
│               ├── config.sh
│               ├── deps.sh
│               ├── services.sh
│               └── verify.sh
└── bin/
    └── installer              ← CLI entry point (symlink to cli.py)

Usage:
  installer run ~/my-project           ← Install/update project
  installer check ~/my-project          ← Check for updates
  installer version ~/my-project        ← Print version
  installer init ~/my-project          ← Initialize installer in project (copy templates)
```

### Key Differences from Current Approach

| Current (Copy-Paste) | New (CLI-agent-installer) |
|---|---|
| `install/` folder exists in each project | **Single package** installed system-wide |
| `install.sh` calls local scripts | `install.sh` calls `installer` CLI |
| `version.sh`, `sync.sh` copied per project | **Shared code** — update once, benefit all |
| Version management duplicated | **Centralized** in `core/` modules |
| Not easily reusable across projects | **Universal** — any Python project |

### Manifest.json Template

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
  ],
  "services": {
    "qdrant": {"port": 6333, "required": true}
  }
}
```

### CLI Usage Examples

```bash
# 1. Initialize installer in a project
cd ~/my-project
installer init .

# This creates:
#   - install/manifest.json  ← customized for your project
#   - install.sh              ← thin wrapper that calls installer CLI
#   - install/update.sh       ← optional: custom orchestration logic

# 2. Install/update project (from anywhere)
installer run ~/my-project

# 3. Check for updates
installer check ~/my-project

# 4. Print local/remote versions
installer version ~/my-project
installer version --remote ~/my-project
```

### Install.sh (Thin Wrapper)

```bash
#!/bin/bash
# install.sh — Thin wrapper for CLI-agent-installer
# Usage: bash install.sh [install_dir]

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="${1:-$HOME/my-project}"

# Check if installer is available
if command -v installer &>/dev/null; then
    installer run "$INSTALL_DIR"
else
    echo "⚠️  CLI-agent-installer not found. Installing..."
    curl -fsSL https://raw.githubusercontent.com/Ruben-Alvarez-Dev/CLI-agent-installer/main/install.sh | bash
    installer run "$INSTALL_DIR"
fi
```

### How It Works (End-to-End)

1. **Project Initialization**:
   ```bash
   installer init ~/my-project
   ```
   → Reads `pyproject.toml` or asks user for repo name
   → Generates `install/manifest.json` with project-specific config
   → Copies `install.sh` thin wrapper
   → (Optional) Copies `install/update.sh` template

2. **Installation**:
   ```bash
   bash install.sh ~/my-project
   ```
   → Wrapper calls `installer run ~/my-project`
   → `installer` reads `manifest.json`
   → Detects mode (install/update/repair)
   → Executes: backup → sync → deps → verify

3. **Update Check**:
   ```bash
   installer check ~/my-project
   ```
   → Reads local version from manifest
   → Queries GitHub API for latest release
   → Compares and reports status

### Benefits

| Benefit | Explanation |
|---|---|
| **DRY (Don't Repeat Yourself)** | Installer logic exists in ONE place |
| **Updates benefit all projects** | Fix a bug in installer → all projects get fix on next pip upgrade |
| **Easy to add features** | Add new core module → automatically available to all projects |
| **Consistent UX** | Same CLI, same behavior across all projects |
| **Less maintenance** | No need to copy-paste `install/` folders |
| **Better testing** | One test suite for installer, not N test suites per project |

### Dependencies

- **Runtime**: `requests` (for GitHub API), `click` (CLI)
- **Python**: 3.12+
- **System**: `curl`, `bash`, `git` (optional, for git-based installs)

### Installation Options

1. **From PyPI** (recommended):
   ```bash
   pip install CLI-agent-installer
   installer init ~/my-project
   ```

2. **From source**:
   ```bash
   git clone https://github.com/Ruben-Alvarez-Dev/CLI-agent-installer
   cd CLI-agent-installer
   pip install -e .
   ```

3. **One-liner** (for users without pip):
   ```bash
   curl -fsSL https://raw.githubusercontent.com/Ruben-Alvarez-Dev/CLI-agent-installer/main/install.sh | bash
   ```

### Migration Path (from current install/)

**For existing projects (MCP-agent-memory, CLI-agent-memory):**

1. Install CLI-agent-installer:
   ```bash
   pip install CLI-agent-installer
   ```

2. Replace local `install/` with thin wrappers:
   ```bash
   rm -rf install/
   installer init .
   ```

3. Commit changes:
   ```bash
   git add install.sh install/manifest.json
   git commit -m "feat: switch to CLI-agent-installer"
   ```

**No data loss** — the new installer preserves user data (`data/`, `config/`, etc.)

---

## Implementation Phases

1. **Phase 1: Core Package Structure**
   - Create `pyproject.toml`
   - Create `src/cli_agent_installer/` with CLI entry point
   - Implement `core/version.py`, `core/manifest.py`, `core/sync.py`

2. **Phase 2: CLI Interface**
   - Implement `cli.py` with commands: `init`, `run`, `check`, `version`
   - Add `--help`, `--verbose`, `--dry-run` flags

3. **Phase 3: Templates**
   - Create `templates/manifest.json`, `templates/install.sh`, `templates/install/update.sh`
   - Implement `init` command to generate project-specific files

4. **Phase 4: Migration Scripts**
   - Write migration guide for existing projects
   - Test migration on MCP-agent-memory and CLI-agent-memory

5. **Phase 5: Distribution**
   - Publish to PyPI
   - Create GitHub repository
   - Write documentation

---

## Questions & Decisions Needed

1. **What services should `services.py` manage?**
   - Currently: Qdrant, llama-server
   - Should this be generic or project-specific?
   - Decision: Keep generic but allow projects to define custom services in `manifest.json`

2. **How to handle project-specific scripts?**
   - Option A: Projects can override default scripts by placing `install/custom.sh`
   - Option B: Use hooks in manifest.json
   - Decision: Option A (simpler, more flexible)

3. **What about non-Python projects?**
   - Initial focus: Python projects
   - Can extend later (Node.js, Rust, etc.)
   - Decision: Python-only for v1.0

4. **How to handle dependencies installation?**
   - Current: 3 strategies (wheels, pip, download)
   - New: Should we support pipx? uv?
   - Decision: Support pip (default), allow override in manifest

---

## Next Steps

1. Create `pyproject.toml` for CLI-agent-installer
2. Implement `core/version.py` (version reading, GitHub API)
3. Implement `core/manifest.py` (manifest loading, validation)
4. Implement `core/sync.py` (sync logic, zombie removal)
5. Implement `cli.py` with basic commands
6. Create templates
7. Test on MCP-agent-memory
8. Test on CLI-agent-memory
9. Publish to PyPI
