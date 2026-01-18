"""
State Manager for VSM Orchestrator

Handles persistence of state files for cross-agent communication.
State is stored in .claude/vsm-state/ directory.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, asdict, field


def get_state_dir() -> Path:
    """Get the VSM state directory, creating it if necessary."""
    state_dir = Path.cwd() / ".claude" / "vsm-state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


@dataclass
class CurrentTask:
    """Active task definition."""
    id: str
    description: str
    created_at: str
    status: str = "pending"  # pending, in_progress, completed, failed
    complexity: str = "unknown"  # simple, medium, complex
    assigned_agents: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class AgentStatus:
    """Status of an S1 agent."""
    name: str
    type: str  # generalist, functional, domain
    status: str = "available"  # available, busy, error
    current_task: Optional[str] = None
    error_count: int = 0
    success_count: int = 0


@dataclass
class ViabilityMetrics:
    """System health metrics for VSM viability."""
    window: str = "last_10_tasks"
    completion_rate: float = 1.0
    agent_errors: dict = field(default_factory=dict)
    oscillation_rate: float = 0.0
    audit_pass_rate: float = 1.0
    s3_s4_conflicts: int = 0
    avg_cycle_iterations: float = 1.0
    active_adaptations: list = field(default_factory=list)
    last_updated: str = ""

    def update_timestamp(self):
        self.last_updated = datetime.utcnow().isoformat()


@dataclass
class S3Allocation:
    """Resource allocation decision from S3."""
    task_id: str
    complexity: str
    selected_agents: list
    rationale: str
    created_at: str
    parallel_execution: bool = False


@dataclass
class S4Environment:
    """External context and research from S4."""
    task_id: str
    analysis: str
    external_context: list = field(default_factory=list)
    risks: list = field(default_factory=list)
    opportunities: list = field(default_factory=list)
    recommended_approach: str = ""
    created_at: str = ""


class StateManager:
    """Manages VSM state files."""

    def __init__(self, state_dir: Optional[Path] = None):
        self.state_dir = state_dir or get_state_dir()
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _read_json(self, filename: str) -> Optional[dict]:
        """Read a JSON state file."""
        filepath = self.state_dir / filename
        if not filepath.exists():
            return None
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def _write_json(self, filename: str, data: Any) -> None:
        """Write data to a JSON state file."""
        filepath = self.state_dir / filename
        with open(filepath, 'w') as f:
            if hasattr(data, '__dataclass_fields__'):
                json.dump(asdict(data), f, indent=2, default=str)
            else:
                json.dump(data, f, indent=2, default=str)

    # Current Task Management
    def get_current_task(self) -> Optional[CurrentTask]:
        """Get the current active task."""
        data = self._read_json("current-task.json")
        if data:
            return CurrentTask(**data)
        return None

    def set_current_task(self, task: CurrentTask) -> None:
        """Set the current active task."""
        self._write_json("current-task.json", task)

    def clear_current_task(self) -> None:
        """Clear the current task (task completed)."""
        filepath = self.state_dir / "current-task.json"
        if filepath.exists():
            filepath.unlink()

    # Viability Metrics
    def get_viability_metrics(self) -> ViabilityMetrics:
        """Get current viability metrics."""
        data = self._read_json("viability-metrics.json")
        if data:
            return ViabilityMetrics(**data)
        return ViabilityMetrics()

    def update_viability_metrics(self, metrics: ViabilityMetrics) -> None:
        """Update viability metrics."""
        metrics.update_timestamp()
        self._write_json("viability-metrics.json", metrics)

    def record_agent_result(self, agent_name: str, success: bool) -> None:
        """Record an agent's task result for metrics."""
        metrics = self.get_viability_metrics()

        if agent_name not in metrics.agent_errors:
            metrics.agent_errors[agent_name] = 0.0

        # Update rolling error rate (simple exponential moving average)
        alpha = 0.2
        error_value = 0.0 if success else 1.0
        metrics.agent_errors[agent_name] = (
            alpha * error_value + (1 - alpha) * metrics.agent_errors[agent_name]
        )

        self.update_viability_metrics(metrics)

    def record_task_completion(self, success: bool) -> None:
        """Record task completion for metrics."""
        metrics = self.get_viability_metrics()

        # Update rolling completion rate
        alpha = 0.1
        completion_value = 1.0 if success else 0.0
        metrics.completion_rate = (
            alpha * completion_value + (1 - alpha) * metrics.completion_rate
        )

        self.update_viability_metrics(metrics)

    def record_oscillation(self) -> None:
        """Record an oscillation event (reverted changes)."""
        metrics = self.get_viability_metrics()
        alpha = 0.15
        metrics.oscillation_rate = alpha + (1 - alpha) * metrics.oscillation_rate
        self.update_viability_metrics(metrics)

    def record_audit_result(self, passed: bool) -> None:
        """Record an audit result."""
        metrics = self.get_viability_metrics()
        alpha = 0.15
        audit_value = 1.0 if passed else 0.0
        metrics.audit_pass_rate = (
            alpha * audit_value + (1 - alpha) * metrics.audit_pass_rate
        )
        self.update_viability_metrics(metrics)

    def record_s3_s4_conflict(self) -> None:
        """Record a conflict between S3 and S4."""
        metrics = self.get_viability_metrics()
        metrics.s3_s4_conflicts += 1
        self.update_viability_metrics(metrics)

    # Agent Registry
    def get_agent_registry(self) -> dict:
        """Get the registry of available S1 agents."""
        data = self._read_json("agent-registry.json")
        if data:
            return data
        # Return default registry
        return self._create_default_registry()

    def _create_default_registry(self) -> dict:
        """Create the default agent registry."""
        registry = {
            "agents": {
                "generalist-coder": {
                    "type": "generalist",
                    "status": "available",
                    "capabilities": ["general coding", "simple fixes", "small features"]
                },
                "code-writer": {
                    "type": "functional",
                    "status": "available",
                    "capabilities": ["implementation", "new features", "code generation"]
                },
                "tester": {
                    "type": "functional",
                    "status": "available",
                    "capabilities": ["unit tests", "integration tests", "test coverage"]
                },
                "reviewer": {
                    "type": "functional",
                    "status": "available",
                    "capabilities": ["code review", "best practices", "quality checks"]
                },
                "documenter": {
                    "type": "functional",
                    "status": "available",
                    "capabilities": ["documentation", "comments", "API docs"]
                },
                "frontend": {
                    "type": "domain",
                    "status": "available",
                    "capabilities": ["UI/UX", "React", "CSS", "accessibility"]
                },
                "backend": {
                    "type": "domain",
                    "status": "available",
                    "capabilities": ["APIs", "services", "business logic"]
                },
                "database": {
                    "type": "domain",
                    "status": "available",
                    "capabilities": ["SQL", "migrations", "data modeling", "queries"]
                },
                "infrastructure": {
                    "type": "domain",
                    "status": "available",
                    "capabilities": ["DevOps", "CI/CD", "deployment", "containers"]
                }
            },
            "last_updated": datetime.utcnow().isoformat()
        }
        self._write_json("agent-registry.json", registry)
        return registry

    def update_agent_status(self, agent_name: str, status: str,
                           current_task: Optional[str] = None) -> None:
        """Update an agent's status."""
        registry = self.get_agent_registry()
        if agent_name in registry["agents"]:
            registry["agents"][agent_name]["status"] = status
            registry["agents"][agent_name]["current_task"] = current_task
            registry["last_updated"] = datetime.utcnow().isoformat()
            self._write_json("agent-registry.json", registry)

    # S3 Allocations
    def get_s3_allocation(self) -> Optional[S3Allocation]:
        """Get current S3 resource allocation."""
        data = self._read_json("s3-allocations.json")
        if data:
            return S3Allocation(**data)
        return None

    def set_s3_allocation(self, allocation: S3Allocation) -> None:
        """Set S3 resource allocation."""
        self._write_json("s3-allocations.json", allocation)

    # S4 Environment
    def get_s4_environment(self) -> Optional[S4Environment]:
        """Get S4 environment analysis."""
        data = self._read_json("s4-environment.json")
        if data:
            return S4Environment(**data)
        return None

    def set_s4_environment(self, environment: S4Environment) -> None:
        """Set S4 environment analysis."""
        self._write_json("s4-environment.json", environment)

    # Utility Methods
    def get_all_state(self) -> dict:
        """Get all state as a dictionary."""
        return {
            "current_task": self._read_json("current-task.json"),
            "viability_metrics": self._read_json("viability-metrics.json"),
            "agent_registry": self._read_json("agent-registry.json"),
            "s3_allocation": self._read_json("s3-allocations.json"),
            "s4_environment": self._read_json("s4-environment.json")
        }

    def reset_state(self) -> None:
        """Reset all state (for testing or fresh start)."""
        for filename in ["current-task.json", "viability-metrics.json",
                        "agent-registry.json", "s3-allocations.json",
                        "s4-environment.json"]:
            filepath = self.state_dir / filename
            if filepath.exists():
                filepath.unlink()
