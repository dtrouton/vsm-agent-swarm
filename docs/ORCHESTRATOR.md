# Python Orchestrator Documentation

The `orchestrator/` module is the Python implementation of the VSM control loop. It can be used standalone or integrated with the Claude Code plugin.

## Installation

**Requirements:** Python 3.13+

The orchestrator uses only Python standard library - no external dependencies required.

```bash
cd vsm-orchestrator
python -m orchestrator --help
```

## Command Line Interface

### Running a Task

```bash
# Basic usage
python -m orchestrator "Add a login feature"

# With complexity hint
python -m orchestrator --simple "Fix typo in README"
python -m orchestrator --medium "Add user validation"
python -m orchestrator --complex "Implement OAuth2"

# Verbose output
python -m orchestrator -v "Task description"

# Specify working directory
python -m orchestrator -d /path/to/project "Task description"
```

### Viewing State

```bash
# Human-readable state
python -m orchestrator --state

# JSON format
python -m orchestrator --state --json
```

Output:
```
============================================================
VSM State
============================================================

Current Task:
  ID: a1b2c3d4
  Description: Add user authentication...
  Status: completed
  Complexity: medium

Viability Metrics:
  Completion Rate: 85.00%
  Audit Pass Rate: 92.00%
  Oscillation Rate: 8.00%
  S3/S4 Conflicts: 2

  Agent Error Rates:
    code-writer: 5.00%
    tester: 15.00%

  Active Adaptations:
    - add_review_step: Add reviewer before tester
============================================================
```

### Viewing Execution Log

```bash
# Last 20 entries
python -m orchestrator --log

# Last 50 entries
python -m orchestrator --log --log-count=50

# JSON format
python -m orchestrator --log --json
```

### Resetting State

```bash
python -m orchestrator --reset
```

## Module Reference

### orchestrator.state_manager

Manages persistence of VSM state files.

```python
from orchestrator import StateManager, CurrentTask, ViabilityMetrics

# Initialize
state = StateManager()

# Current task
task = CurrentTask(
    id="abc123",
    description="Add feature X",
    created_at="2024-01-15T10:00:00Z",
    status="in_progress",
    complexity="medium"
)
state.set_current_task(task)
task = state.get_current_task()
state.clear_current_task()

# Viability metrics
metrics = state.get_viability_metrics()
state.update_viability_metrics(metrics)

# Record events
state.record_agent_result("code-writer", success=True)
state.record_task_completion(success=True)
state.record_oscillation()
state.record_audit_result(passed=True)
state.record_s3_s4_conflict()

# Agent registry
registry = state.get_agent_registry()
state.update_agent_status("code-writer", "busy", current_task="abc123")

# S3 allocations
from orchestrator.state_manager import S3Allocation
allocation = S3Allocation(
    task_id="abc123",
    complexity="medium",
    selected_agents=["code-writer", "tester"],
    rationale="Multi-file feature requiring tests",
    created_at="2024-01-15T10:00:00Z"
)
state.set_s3_allocation(allocation)
allocation = state.get_s3_allocation()

# S4 environment
from orchestrator.state_manager import S4Environment
env = S4Environment(
    task_id="abc123",
    analysis="Task involves user authentication...",
    risks=[{"risk": "Security", "severity": "high"}],
    opportunities=[],
    recommended_approach="Use JWT tokens"
)
state.set_s4_environment(env)
env = state.get_s4_environment()

# Utilities
all_state = state.get_all_state()  # Returns dict with all state
state.reset_state()  # Clears all state files
```

#### Data Classes

```python
@dataclass
class CurrentTask:
    id: str
    description: str
    created_at: str
    status: str = "pending"  # pending, in_progress, completed, failed
    complexity: str = "unknown"  # simple, medium, complex
    assigned_agents: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

@dataclass
class ViabilityMetrics:
    window: str = "last_10_tasks"
    completion_rate: float = 1.0
    agent_errors: dict = field(default_factory=dict)  # {agent: error_rate}
    oscillation_rate: float = 0.0
    audit_pass_rate: float = 1.0
    s3_s4_conflicts: int = 0
    avg_cycle_iterations: float = 1.0
    active_adaptations: list = field(default_factory=list)
    last_updated: str = ""

@dataclass
class S3Allocation:
    task_id: str
    complexity: str
    selected_agents: list
    rationale: str
    created_at: str
    parallel_execution: bool = False

@dataclass
class S4Environment:
    task_id: str
    analysis: str
    external_context: list = field(default_factory=list)
    risks: list = field(default_factory=list)
    opportunities: list = field(default_factory=list)
    recommended_approach: str = ""
    created_at: str = ""
```

### orchestrator.execution_log

Append-only JSONL execution log for audit trail.

```python
from orchestrator import ExecutionLog, LogEventType

# Initialize
log = ExecutionLog()
print(f"Session ID: {log.session_id}")

# Log events
log.log_task_started("abc123", "Add feature X", complexity="medium")
log.log_task_completed("abc123", success=True, summary="Feature added")

log.log_agent_invoked("s1-code-writer", "abc123", prompt="Implement...")
log.log_agent_completed("s1-code-writer", "abc123", success=True)

log.log_allocation("abc123", "medium", ["code-writer", "tester"], "rationale")
log.log_audit("abc123", passed=True, findings=[])
log.log_conflict("abc123", "Use generalist", "Need specialist")
log.log_policy_decision("abc123", "Use specialist", "Security critical")
log.log_adaptation("add_review_step", "high_errors", "Add reviewer")
log.log_oscillation("abc123", "File reverted twice")

# Query log
entries = log.read_all()
entries = log.read_session()  # Current session only
entries = log.read_session("specific-session-id")
entries = log.read_task("abc123")
entries = log.read_recent(count=50)

# Task summary
summary = log.get_task_summary("abc123")
# Returns: {task_id, started_at, completed_at, status, agents_invoked, ...}

# Iterate without loading all
for entry in log.iter_entries():
    print(entry.event_type)

# Clear (use with caution)
log.clear()
```

#### Log Entry Structure

```python
@dataclass
class LogEntry:
    timestamp: str
    event_type: str
    task_id: Optional[str]
    agent: Optional[str]
    data: dict
    session_id: str
```

#### Event Types

```python
class LogEventType(str, Enum):
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
```

### orchestrator.complexity_analyzer

Analyzes task complexity to guide agent selection.

```python
from orchestrator import ComplexityAnalyzer, Complexity

# Initialize (optionally with current metrics for adaptive thresholds)
analyzer = ComplexityAnalyzer()
# or
analyzer = ComplexityAnalyzer(viability_metrics={
    "agent_errors": {"tester": 0.25},
    "oscillation_rate": 0.15
})

# Analyze a task
assessment = analyzer.analyze("Add user authentication with OAuth2")

print(assessment.complexity)        # Complexity.COMPLEX
print(assessment.confidence)        # 0.85
print(assessment.rationale)         # "Keywords suggest complex; Domain: backend"
print(assessment.suggested_agents)  # ["backend", "tester", "reviewer"]
print(assessment.parallel_possible) # False
print(assessment.keywords_found)    # ["authentication"]
print(assessment.domain_signals)    # ["backend"]
print(assessment.scope_estimate)    # "multi_file"

# With user hint
assessment = analyzer.analyze("Quick fix", user_hint="simple")
# Returns simple with 0.95 confidence

# Get agent recommendation
recommendation = analyzer.get_agent_recommendation(assessment)
# Returns dict suitable for S3 allocation:
# {
#   "complexity": "complex",
#   "confidence": 0.85,
#   "primary_agents": ["backend", "tester"],
#   "support_agents": ["reviewer"],
#   "parallel_execution": False,
#   ...
# }
```

#### Complexity Levels

```python
class Complexity(str, Enum):
    SIMPLE = "simple"   # Single agent, quick fixes
    MEDIUM = "medium"   # Functional specialists
    COMPLEX = "complex" # Domain specialists
```

### orchestrator.adaptation

Automatic adaptation based on viability metrics.

```python
from orchestrator.adaptation import AdaptationEngine, AdaptationType

# Initialize
state = StateManager()
engine = AdaptationEngine(state)

# Analyze metrics and get needed adaptations
metrics = state.get_viability_metrics()
adaptations = engine.analyze_metrics(metrics)

for adaptation in adaptations:
    print(f"{adaptation.type}: {adaptation.effect}")

# Apply adaptations (updates metrics.active_adaptations)
engine.apply_adaptations(adaptations)

# Check active adaptations
active = engine.get_active_adaptations()

# Query specific adaptations
if engine.should_add_review_step("tester"):
    print("Add reviewer before tester")

if engine.should_require_s5_approval():
    print("S5 approval required for allocations")

if engine.should_increase_s2():
    print("Increase coordination")

if engine.should_parallelize():
    print("Can parallelize S1 agents")

# Get complexity threshold adjustment
adjustment = engine.get_complexity_adjustment()  # Returns -0.15 to lower thresholds

# Clear an adaptation
engine.clear_adaptation(AdaptationType.ADD_REVIEW_STEP)
```

#### Adaptation Types

```python
class AdaptationType(str, Enum):
    ADD_REVIEW_STEP = "add_review_step"
    LOWER_COMPLEXITY_THRESHOLD = "lower_complexity_threshold"
    INCREASE_S2_INVOLVEMENT = "increase_s2_involvement"
    REQUIRE_S5_APPROVAL = "require_s5_approval"
    PARALLELIZE_S1 = "parallelize_s1"
    TIGHTEN_S3_STAR = "tighten_s3_star"
```

#### Thresholds

| Adaptation | Trigger Condition |
|------------|-------------------|
| Add review step | Agent error rate > 30% |
| Lower complexity threshold | Completion rate < 50% |
| Increase S2 | Oscillation rate > 20% |
| Require S5 approval | S3/S4 conflicts > 3 |
| Parallelize S1 | Avg cycle iterations > 1.5 |
| Tighten S3* | Audit pass rate < 80% |

### orchestrator.vsm_loop

The main VSM control loop.

```python
from orchestrator.vsm_loop import VSMLoop, VSMCycleResult
import asyncio

# Initialize
loop = VSMLoop(
    working_dir=Path("/path/to/project"),
    claude_command="claude"  # CLI command to invoke
)

# Run a cycle
async def run():
    result = await loop.run_cycle(
        task="Add user authentication",
        task_id=None,  # Auto-generated if not provided
        complexity_hint="complex"  # Optional
    )
    return result

result = asyncio.run(run())

print(result.task_id)        # "a1b2c3d4"
print(result.success)        # True
print(result.summary)        # "Completed with 3/3 agents successful"
print(result.agents_invoked) # ["s1-backend", "s1-tester", "s1-reviewer"]
print(result.audit_passed)   # True
print(result.conflicts)      # []
print(result.adaptations)    # [{"type": "...", ...}]
print(result.s1_results)     # [AgentResult, ...]
```

#### Result Types

```python
@dataclass
class AgentResult:
    agent: str
    success: bool
    output: str
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

@dataclass
class VSMCycleResult:
    task_id: str
    success: bool
    summary: str
    agents_invoked: List[str]
    audit_passed: Optional[bool] = None
    conflicts: List[dict] = field(default_factory=list)
    adaptations: List[dict] = field(default_factory=list)
    s1_results: List[AgentResult] = field(default_factory=list)
```

## Programmatic Usage

### Basic Example

```python
import asyncio
from pathlib import Path
from orchestrator import StateManager, ExecutionLog, ComplexityAnalyzer
from orchestrator.vsm_loop import VSMLoop

async def run_vsm_task(task: str, project_path: str):
    """Run a VSM-orchestrated task programmatically."""

    # Initialize components
    loop = VSMLoop(working_dir=Path(project_path))

    # Run the cycle
    result = await loop.run_cycle(task)

    # Check result
    if result.success:
        print(f"Task completed successfully!")
        print(f"Agents used: {', '.join(result.agents_invoked)}")
    else:
        print(f"Task failed: {result.summary}")
        for agent_result in result.s1_results:
            if not agent_result.success:
                print(f"  {agent_result.agent}: {agent_result.error}")

    return result

# Run it
result = asyncio.run(run_vsm_task(
    "Add input validation to the login form",
    "/path/to/my/project"
))
```

### Monitoring Example

```python
from orchestrator import StateManager, ExecutionLog

def monitor_vsm_health():
    """Check VSM system health."""
    state = StateManager()
    metrics = state.get_viability_metrics()

    # Check for issues
    issues = []

    if metrics.completion_rate < 0.7:
        issues.append(f"Low completion rate: {metrics.completion_rate:.0%}")

    if metrics.audit_pass_rate < 0.8:
        issues.append(f"Low audit pass rate: {metrics.audit_pass_rate:.0%}")

    if metrics.oscillation_rate > 0.2:
        issues.append(f"High oscillation: {metrics.oscillation_rate:.0%}")

    for agent, error_rate in metrics.agent_errors.items():
        if error_rate > 0.3:
            issues.append(f"Agent {agent} has {error_rate:.0%} error rate")

    if issues:
        print("VSM Health Issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("VSM system is healthy")

    # Show active adaptations
    if metrics.active_adaptations:
        print("\nActive Adaptations:")
        for a in metrics.active_adaptations:
            print(f"  - {a['type']}: {a['effect']}")

monitor_vsm_health()
```

### Custom Complexity Rules

```python
from orchestrator.complexity_analyzer import (
    ComplexityAnalyzer,
    COMPLEXITY_KEYWORDS,
    DOMAIN_PATTERNS,
    Complexity
)

# Add custom keywords
COMPLEXITY_KEYWORDS[Complexity.COMPLEX].extend([
    r"\bmachine\s+learning\b",
    r"\bai\b",
    r"\bml\b"
])

# Add custom domain
DOMAIN_PATTERNS["ml"] = [
    r"\bmodel\b",
    r"\btraining\b",
    r"\binference\b",
    r"\btensor\b",
    r"\bpytorch\b",
    r"\btensorflow\b"
]

# Use modified analyzer
analyzer = ComplexityAnalyzer()
assessment = analyzer.analyze("Train ML model for predictions")
print(assessment.domain_signals)  # ["ml"]
```

## State File Locations

All state is stored in `.claude/vsm-state/` relative to the working directory:

| File | Purpose |
|------|---------|
| `current-task.json` | Active task details |
| `viability-metrics.json` | System health metrics |
| `agent-registry.json` | Available agents and status |
| `execution-log.jsonl` | Append-only audit trail |
| `s3-allocations.json` | Current resource allocation |
| `s4-environment.json` | Strategic analysis |

## Environment Variables

The orchestrator respects these environment variables (set by Claude Code):

| Variable | Description |
|----------|-------------|
| `CLAUDE_SESSION_ID` | Current session identifier |
| `CLAUDE_PLUGIN_ROOT` | Plugin installation directory |
