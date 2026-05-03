#!/usr/bin/env python3
"""Simple test for StructuredLogger."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cli_agent_installer.core.log import StructuredLogger

logger = StructuredLogger("/tmp/test-logs")

logger.info("System starting", extra={"pid": 123})
logger.error("Test error", extra={"code": 500})
logger.warning("Test warning")

logs = logger.get_logs()
print(f"Logged {len(logs)} entries")
for log in logs:
    print(f"  {log.level}: {log.message}")
