#!/usr/bin/env python3
"""
Log System Agent Hook

Logs higher-level VSM system agent (S2-S5) completions.
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def get_log_file() -> Path:
    """Get the VSM execution log file path."""
    state_dir = Path.cwd() / ".claude" / "vsm-state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / "execution-log.jsonl"


def log_system_agent(agent_name: str, status: str) -> None:
    """Log a system agent completion."""
    log_file = get_log_file()

    # Determine the VSM system level
    system_level = "unknown"
    if "system5" in agent_name or "policy" in agent_name:
        system_level = "S5-Policy"
    elif "system4" in agent_name or "strategy" in agent_name:
        system_level = "S4-Intelligence"
    elif "audit" in agent_name or "system3-audit" in agent_name:
        system_level = "S3*-Audit"
    elif "system3" in agent_name or "control" in agent_name:
        system_level = "S3-Control"
    elif "system2" in agent_name or "coordination" in agent_name:
        system_level = "S2-Coordination"

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "system_agent_completed",
        "agent": agent_name,
        "system_level": system_level,
        "status": status
    }

    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        agent_name = sys.argv[1]
        status = sys.argv[2]
        log_system_agent(agent_name, status)
