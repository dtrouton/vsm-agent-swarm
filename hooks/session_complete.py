#!/usr/bin/env python3
"""
Session Complete Hook

Called when a VSM session completes.
Updates final metrics and logs session end.
"""

import json
from datetime import datetime
from pathlib import Path


def get_state_dir() -> Path:
    """Get the VSM state directory."""
    state_dir = Path.cwd() / ".claude" / "vsm-state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def log_session_complete() -> None:
    """Log session completion and update metrics."""
    state_dir = get_state_dir()
    log_file = state_dir / "execution-log.jsonl"
    metrics_file = state_dir / "viability-metrics.json"

    # Log session end
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "session_complete"
    }
    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + "\n")

    # Update metrics timestamp
    if metrics_file.exists():
        try:
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
            metrics["last_updated"] = datetime.utcnow().isoformat()
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
        except:
            pass

    # Clear current task if completed
    task_file = state_dir / "current-task.json"
    if task_file.exists():
        try:
            with open(task_file, 'r') as f:
                task = json.load(f)
            if task.get("status") in ["completed", "failed"]:
                task_file.unlink()
        except:
            pass


if __name__ == "__main__":
    log_session_complete()
