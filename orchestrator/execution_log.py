"""
Execution Log for VSM Orchestrator

Append-only JSONL log for audit trail of all VSM operations.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Iterator
from dataclasses import dataclass, asdict
from enum import Enum


class LogEventType(str, Enum):
    """Types of log events."""
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    AGENT_INVOKED = "agent_invoked"
    AGENT_COMPLETED = "agent_completed"
    AGENT_ERROR = "agent_error"
    STATE_CHANGED = "state_changed"
    ALLOCATION_MADE = "allocation_made"
    AUDIT_PERFORMED = "audit_performed"
    CONFLICT_DETECTED = "conflict_detected"
    POLICY_DECISION = "policy_decision"
    ADAPTATION_APPLIED = "adaptation_applied"
    OSCILLATION_DETECTED = "oscillation_detected"


@dataclass
class LogEntry:
    """A single log entry."""
    timestamp: str
    event_type: str
    task_id: Optional[str]
    agent: Optional[str]
    data: dict
    session_id: str

    @classmethod
    def create(cls, event_type: LogEventType, task_id: Optional[str] = None,
               agent: Optional[str] = None, data: Optional[dict] = None,
               session_id: str = "") -> "LogEntry":
        """Create a new log entry with current timestamp."""
        return cls(
            timestamp=datetime.utcnow().isoformat(),
            event_type=event_type.value,
            task_id=task_id,
            agent=agent,
            data=data or {},
            session_id=session_id
        )

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_json(cls, json_str: str) -> "LogEntry":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls(**data)


class ExecutionLog:
    """Append-only execution log for VSM operations."""

    def __init__(self, state_dir: Optional[Path] = None, session_id: Optional[str] = None):
        from .state_manager import get_state_dir
        self.state_dir = state_dir or get_state_dir()
        self.log_file = self.state_dir / "execution-log.jsonl"
        self.session_id = session_id or self._generate_session_id()

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        import hashlib
        timestamp = datetime.utcnow().isoformat()
        return hashlib.sha256(timestamp.encode()).hexdigest()[:12]

    def append(self, entry: LogEntry) -> None:
        """Append an entry to the log."""
        entry.session_id = self.session_id
        with open(self.log_file, 'a') as f:
            f.write(entry.to_json() + "\n")

    def log(self, event_type: LogEventType, task_id: Optional[str] = None,
            agent: Optional[str] = None, **data) -> None:
        """Convenience method to log an event."""
        entry = LogEntry.create(
            event_type=event_type,
            task_id=task_id,
            agent=agent,
            data=data,
            session_id=self.session_id
        )
        self.append(entry)

    # Convenience methods for common log events
    def log_task_started(self, task_id: str, description: str, complexity: str = "unknown") -> None:
        """Log task start."""
        self.log(LogEventType.TASK_STARTED, task_id=task_id,
                description=description, complexity=complexity)

    def log_task_completed(self, task_id: str, success: bool = True,
                          summary: str = "") -> None:
        """Log task completion."""
        event = LogEventType.TASK_COMPLETED if success else LogEventType.TASK_FAILED
        self.log(event, task_id=task_id, success=success, summary=summary)

    def log_agent_invoked(self, agent: str, task_id: str, prompt: str = "") -> None:
        """Log agent invocation."""
        self.log(LogEventType.AGENT_INVOKED, task_id=task_id, agent=agent,
                prompt_preview=prompt[:200] if prompt else "")

    def log_agent_completed(self, agent: str, task_id: str, success: bool = True,
                           result_summary: str = "") -> None:
        """Log agent completion."""
        event = LogEventType.AGENT_COMPLETED if success else LogEventType.AGENT_ERROR
        self.log(event, task_id=task_id, agent=agent, success=success,
                result_summary=result_summary)

    def log_allocation(self, task_id: str, complexity: str,
                      selected_agents: list, rationale: str) -> None:
        """Log S3 allocation decision."""
        self.log(LogEventType.ALLOCATION_MADE, task_id=task_id,
                complexity=complexity, selected_agents=selected_agents,
                rationale=rationale)

    def log_audit(self, task_id: str, passed: bool, findings: list) -> None:
        """Log audit result."""
        self.log(LogEventType.AUDIT_PERFORMED, task_id=task_id,
                passed=passed, findings=findings)

    def log_conflict(self, task_id: str, s3_position: str, s4_position: str) -> None:
        """Log S3/S4 conflict."""
        self.log(LogEventType.CONFLICT_DETECTED, task_id=task_id,
                s3_position=s3_position, s4_position=s4_position)

    def log_policy_decision(self, task_id: str, decision: str, rationale: str) -> None:
        """Log S5 policy decision."""
        self.log(LogEventType.POLICY_DECISION, task_id=task_id,
                decision=decision, rationale=rationale)

    def log_adaptation(self, adaptation_type: str, trigger: str, effect: str) -> None:
        """Log automatic adaptation."""
        self.log(LogEventType.ADAPTATION_APPLIED,
                adaptation_type=adaptation_type, trigger=trigger, effect=effect)

    def log_oscillation(self, task_id: str, details: str) -> None:
        """Log detected oscillation."""
        self.log(LogEventType.OSCILLATION_DETECTED, task_id=task_id, details=details)

    # Query methods
    def read_all(self) -> list[LogEntry]:
        """Read all log entries."""
        if not self.log_file.exists():
            return []
        entries = []
        with open(self.log_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(LogEntry.from_json(line))
        return entries

    def read_session(self, session_id: Optional[str] = None) -> list[LogEntry]:
        """Read log entries for a specific session."""
        target_session = session_id or self.session_id
        return [e for e in self.read_all() if e.session_id == target_session]

    def read_task(self, task_id: str) -> list[LogEntry]:
        """Read log entries for a specific task."""
        return [e for e in self.read_all() if e.task_id == task_id]

    def read_recent(self, count: int = 50) -> list[LogEntry]:
        """Read the most recent log entries."""
        entries = self.read_all()
        return entries[-count:] if len(entries) > count else entries

    def get_task_summary(self, task_id: str) -> dict:
        """Get a summary of a task's execution."""
        entries = self.read_task(task_id)
        if not entries:
            return {"task_id": task_id, "status": "not_found"}

        summary = {
            "task_id": task_id,
            "started_at": None,
            "completed_at": None,
            "status": "unknown",
            "agents_invoked": [],
            "audit_passed": None,
            "conflicts": [],
            "adaptations": []
        }

        for entry in entries:
            if entry.event_type == LogEventType.TASK_STARTED.value:
                summary["started_at"] = entry.timestamp
                summary["status"] = "in_progress"
            elif entry.event_type == LogEventType.TASK_COMPLETED.value:
                summary["completed_at"] = entry.timestamp
                summary["status"] = "completed" if entry.data.get("success") else "failed"
            elif entry.event_type == LogEventType.AGENT_INVOKED.value:
                summary["agents_invoked"].append(entry.agent)
            elif entry.event_type == LogEventType.AUDIT_PERFORMED.value:
                summary["audit_passed"] = entry.data.get("passed")
            elif entry.event_type == LogEventType.CONFLICT_DETECTED.value:
                summary["conflicts"].append(entry.data)
            elif entry.event_type == LogEventType.ADAPTATION_APPLIED.value:
                summary["adaptations"].append(entry.data)

        return summary

    def iter_entries(self) -> Iterator[LogEntry]:
        """Iterate over log entries without loading all into memory."""
        if not self.log_file.exists():
            return
        with open(self.log_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    yield LogEntry.from_json(line)

    def clear(self) -> None:
        """Clear the log file. Use with caution."""
        if self.log_file.exists():
            self.log_file.unlink()
