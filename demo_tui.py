#!/usr/bin/env python3
"""Interactive TUI Demo for CLI-agent-installer v2.0

This script simulates the TUI experience in a terminal without
requiring the full Textual library or terminal support.
"""

import time
import sys
from datetime import datetime

class VirtualTUI:
    """Simulates the TUI interface."""

    def __init__(self):
        self.current_screen = "checklist"
        self.checklist_data = {
            "id": f"{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "completed",
            "progress": 100,
            "duration": 0.45,
            "tasks": [
                {"name": "Detection", "steps": 3, "status": "✅"},
                {"name": "Backup", "steps": 3, "status": "✅"},
                {"name": "Sync Code", "steps": 3, "status": "✅"},
                {"name": "Dependencies", "steps": 3, "status": "✅"},
                {"name": "Configuration", "steps": 2, "status": "✅"},
                {"name": "Services", "steps": 2, "status": "✅"},
                {"name": "Verification", "steps": 3, "status": "✅"},
            ]
        }
        self.logs = [
            "[14:00:00] [SYSTEM] Starting checklist execution",
            "[14:00:00] [TASK]   Detection: running",
            "[14:00:00] [STEP]   Detect mode",
            "[14:00:00] [STEP]   Detect system",
            "[14:00:01] [TASK]   Backup: running",
            "[14:00:01] [STEP]   Backup data",
            "[14:00:01] [STEP]   Backup config",
            "[14:00:01] [STEP]   Backup vault",
            "[14:00:02] [TASK]   Sync Code: running",
            "[14:00:02] [STEP]   Download source",
            "[14:00:02] [STEP]   Sync files",
            "[14:00:02] [STEP]   Verify checksum",
            "[14:00:03] [TASK]   Dependencies: running",
            "[14:00:03] [STEP]   Create venv",
            "[14:00:03] [STEP]   Install deps",
            "[14:00:03] [STEP]   Verify deps",
            "[14:00:04] [TASK]   Configuration: running",
            "[14:00:04] [STEP]   Generate .env",
            "[14:00:04] [STEP]   Generate MCP config",
            "[14:00:05] [TASK]   Services: running",
            "[14:00:05] [STEP]   Stop services",
            "[14:00:05] [STEP]   Start services",
        ]
        self.status_data = {
            "project": "test-project",
            "location": "~/test-tui-project",
            "versions": {
                "local": "1.0.0",
                "git": "v1.0.0",
                "remote": "v1.0.0"
            },
            "update_status": "✅ Up to date",
            "last_checklist": {
                "id": self.checklist_data["id"],
                "status": "✅ Completed",
                "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }

    def clear_screen(self):
        """Clear the terminal screen."""
        print("\033[2J\033[H", end="", flush=True)

    def draw_border(self, width=70):
        """Draw a horizontal border."""
        return "╔" + "═" * (width - 2) + "╗"

    def draw_separator(self, width=70):
        """Draw a horizontal separator."""
        return "╠" + "═" * (width - 2) + "╣"

    def center_text(self, text, width=70):
        """Center text within a width."""
        padding = (width - len(text)) // 2
        return " " * padding + text

    def draw_checklist_screen(self):
        """Draw the checklist screen."""
        self.clear_screen()

        width = 70
        print(self.draw_border(width))
        print(self.center_text("CLI-AGENT-INSTALLER v2.0", width))
        print("║" + " " * (width - 2) + "║")
        print("║" + self.center_text(f"Checklist: {self.checklist_data['id']}", width) + "║")
        print("║" + self.center_text(f"Status:    {self.checklist_data['status']}", width) + "║")
        print("║" + self.center_text(f"Progress:  {self.checklist_data['progress']}%", width) + "║")
        print("║" + self.center_text(f"Duration:  {self.checklist_data['duration']}s", width) + "║")
        print("║" + " " * (width - 2) + "║")
        print("║" + " " * 10 + "Tasks:" + " " * (width - 20) + "║")
        print("║" + " " * (width - 2) + "║")

        for task in self.checklist_data["tasks"]:
            task_line = "║" + " " * 12 + f"{task['status']} {task['name']} ({task['steps']} steps)"
            task_line += " " * (width - len(task_line) - 1) + "║"
            print(task_line)

        print("║" + " " * (width - 2) + "║")
        print("║" + self.center_text("Press 'l' for logs, 's' for status, 'q' to quit", width) + "║")
        print(self.draw_border(width))

    def draw_logs_screen(self):
        """Draw the logs screen."""
        self.clear_screen()

        width = 70
        print(self.draw_border(width))
        print(self.center_text(f"LOGS ({len(self.logs)} entries)", width))
        print("║" + " " * (width - 2) + "║")

        for log in self.logs[-15:]:  # Show last 15 logs
            log_line = "║  " + log
            log_line += " " * (width - len(log_line) - 1) + "║"
            print(log_line)

        print("║" + " " * (width - 2) + "║")
        print("║" + self.center_text("Press 'c' for checklist, 's' for status, 'q' to quit", width) + "║")
        print(self.draw_border(width))

    def draw_status_screen(self):
        """Draw the status screen."""
        self.clear_screen()

        width = 70
        print(self.draw_border(width))
        print(self.center_text("PROJECT STATUS", width))
        print("║" + " " * (width - 2) + "║")
        print("║  Project:    " + self.status_data["project"] + " " * (width - 25 - len(self.status_data["project"])) + "║")
        print("║  Location:   " + self.status_data["location"] + " " * (width - 25 - len(self.status_data["location"])) + "║")
        print("║" + " " * (width - 2) + "║")
        print("║  Versions:" + " " * (width - 14) + "║")
        print("║    Local:   " + self.status_data["versions"]["local"] + " " * (width - 30) + "║")
        print("║    Git:     " + self.status_data["versions"]["git"] + " " * (width - 30) + "║")
        print("║    Remote:  " + self.status_data["versions"]["remote"] + " " * (width - 30) + "║")
        print("║" + " " * (width - 2) + "║")
        print("║  Update Status:" + " " * (width - 20) + "║")
        print("║    " + self.status_data["update_status"] + " " * (width - 30) + "║")
        print("║" + " " * (width - 2) + "║")
        print("║  Last Checklist:" + " " * (width - 21) + "║")
        print("║    ID:    " + self.status_data["last_checklist"]["id"] + " " * (width - 30) + "║")
        print("║    Status: " + self.status_data["last_checklist"]["status"] + " " * (width - 30) + "║")
        print("║    Time:   " + self.status_data["last_checklist"]["time"] + " " * (width - 30) + "║")
        print("║" + " " * (width - 2) + "║")
        print("║" + self.center_text("Press 'c' for checklist, 'l' for logs, 'q' to quit", width) + "║")
        print(self.draw_border(width))

    def run(self):
        """Run the interactive TUI demo."""
        print("\n" + "=" * 70)
        print("CLI-AGENT-INSTALLER v2.0 — TUI DEMO")
        print("=" * 70)
        print("\nThis is an interactive simulation of the TUI.")
        print("Use the following keys to navigate:")
        print("  l - Switch to Logs screen")
        print("  s - Switch to Status screen")
        print("  r - Refresh current screen")
        print("  q - Quit")
        print("\nPress any key to start...")
        input()

        while True:
            if self.current_screen == "checklist":
                self.draw_checklist_screen()
            elif self.current_screen == "logs":
                self.draw_logs_screen()
            elif self.current_screen == "status":
                self.draw_status_screen()

            # Get user input
            try:
                choice = input("\n> ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                break

            if choice == 'q':
                print("\n" + "=" * 70)
                print("Thank you for using CLI-agent-installer v2.0 TUI Demo!")
                print("=" * 70)
                break
            elif choice == 'l':
                self.current_screen = "logs"
            elif choice == 's':
                self.current_screen = "status"
            elif choice == 'c':
                self.current_screen = "checklist"
            elif choice == 'r':
                pass  # Just redraw current screen
            else:
                print(f"Unknown command: {choice}")


def main():
    """Main entry point."""
    tui = VirtualTUI()
    tui.run()


if __name__ == "__main__":
    main()
