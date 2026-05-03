# Installation Instructions

## Quick Start

### 1. Install CLI-agent-installer

```bash
pip install CLI-agent-installer
```

Or from source:

```bash
git clone https://github.com/Ruben-Alvarez-Dev/CLI-agent-installer.git
cd CLI-agent-installer
bash install.sh
```

### 2. Install MCP-agent-memory

```bash
git clone https://github.com/Ruben-Alvarez-Dev/MCP-agent-memory.git
cd MCP-agent-memory
bash install.sh
```

### 3. Install CLI-agent-memory

```bash
git clone https://github.com/Ruben-Alvarez-Dev/CLI-agent-memory.git
cd CLI-agent-memory
bash install.sh
```

---

## Using the Installer

### CLI Mode

```bash
# Check for updates
installer check .

# Install/update
bash install.sh

# View version
installer version .

# View logs
installer logs .

# Run checklist
installer checklist run .
```

### TUI Mode

```bash
installer tui .
```

Key bindings:
- `q` - Quit
- `l` - View logs
- `s` - View status
- `r` - Refresh

### REST API Mode

```bash
# Start server
installer serve

# Access Swagger UI
open http://localhost:8000/docs

# Check status
curl http://localhost:8000/projects/~/my-project/status

# Run checklist
curl -X POST http://localhost:8000/projects/~/my-project/checklists/run

# Get logs
curl http://localhost:8000/projects/~/my-project/logs?format=json
```

---

## Troubleshooting

### Installer not found

```bash
# Install from GitHub
curl -fsSL https://raw.githubusercontent.com/Ruben-Alvarez-Dev/CLI-agent-installer/main/install.sh | bash
```

### Permission denied

```bash
chmod +x install.sh
./install.sh
```

### Python version mismatch

```bash
# Ensure Python 3.12+
python3 --version

# Use python3 explicitly
python3 -m pip install CLI-agent-installer
```

---

## Advanced Usage

### Dry-run (preview changes)

```bash
bash install.sh --dry-run
```

### Verbose logging

```bash
bash install.sh --verbose
```

### Skip checklist (legacy mode)

```bash
bash install.sh --no-checklist
```

### Resume from checkpoint

```bash
installer checklist resume . <checklist-id>
```

### Export logs

```bash
# JSON format
installer logs . --export logs.json

# CSV format
installer logs . --export logs.csv

# Filter by type
installer logs . --type ERROR
```
