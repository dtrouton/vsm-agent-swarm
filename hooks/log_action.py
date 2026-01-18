#!/usr/bin/env python3
"""
Log Action Hook

Logs tool usage for VSM observability.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def get_log_file() -> Path:
    """Get the VSM execution log file path."""
    state_dir = Path.cwd() / ".claude" / "vsm-state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / "execution-log.jsonl"


def log_action(tool_name: str, tool_input: str) -> None:
    """Log a tool action."""
    log_file = get_log_file()

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "tool_used",
        "tool_name": tool_name,
        "input_preview": tool_input[:200] if tool_input else "",
        "session_id": os.environ.get("CLAUDE_SESSION_ID", "unknown")
    }

    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        tool_name = sys.argv[1]
        tool_input = sys.argv[2] if len(sys.argv) > 2 else ""
        log_action(tool_name, tool_input)
