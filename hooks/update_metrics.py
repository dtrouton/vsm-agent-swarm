#!/usr/bin/env python3
"""
Update Metrics Hook

Updates viability metrics when S1 agents complete.
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def get_metrics_file() -> Path:
    """Get the VSM metrics file path."""
    state_dir = Path.cwd() / ".claude" / "vsm-state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / "viability-metrics.json"


def load_metrics() -> dict:
    """Load current metrics."""
    metrics_file = get_metrics_file()
    if metrics_file.exists():
        try:
            with open(metrics_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "window": "last_10_tasks",
        "completion_rate": 1.0,
        "agent_errors": {},
        "oscillation_rate": 0.0,
        "audit_pass_rate": 1.0,
        "s3_s4_conflicts": 0,
        "avg_cycle_iterations": 1.0,
        "active_adaptations": [],
        "last_updated": ""
    }


def save_metrics(metrics: dict) -> None:
    """Save metrics."""
    metrics_file = get_metrics_file()
    metrics["last_updated"] = datetime.utcnow().isoformat()
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)


def update_agent_metrics(agent_name: str, status: str) -> None:
    """Update metrics for an S1 agent completion."""
    metrics = load_metrics()

    # Normalize agent name (remove s1- prefix)
    agent_key = agent_name.replace("s1-", "").replace("system1-", "")

    # Initialize agent error rate if not present
    if agent_key not in metrics["agent_errors"]:
        metrics["agent_errors"][agent_key] = 0.0

    # Update error rate using exponential moving average
    alpha = 0.2
    is_error = status.lower() in ["error", "failed", "failure"]
    error_value = 1.0 if is_error else 0.0

    metrics["agent_errors"][agent_key] = (
        alpha * error_value + (1 - alpha) * metrics["agent_errors"][agent_key]
    )

    save_metrics(metrics)

    # Log the update
    log_file = Path.cwd() / ".claude" / "vsm-state" / "execution-log.jsonl"
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "agent_completed",
        "agent": agent_name,
        "status": status,
        "error_rate_after": metrics["agent_errors"][agent_key]
    }
    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        agent_name = sys.argv[1]
        status = sys.argv[2]
        update_agent_metrics(agent_name, status)
