# VSM Orchestrator Architecture

This document describes the technical architecture of the VSM Multi-Agent Orchestrator.

## Overview

The VSM Orchestrator implements Stafford Beer's Viable Systems Model as a multi-agent coordination system. The architecture consists of:

1. **Claude Code Plugin** - Agent definitions, commands, hooks
2. **Python Orchestrator** - Control loop, state management, adaptation
3. **State Layer** - File-based persistence for cross-agent communication

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Claude Code CLI                                │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      VSM Plugin                                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐│   │
│  │  │ Commands │  │  Skills  │  │  Hooks   │  │     Agents       ││   │
│  │  │  /vsm    │  │ vsm-orch │  │ logging  │  │ S1-S5 definitions││   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Python Orchestrator                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │  VSM Loop    │  │    State     │  │  Execution   │  │ Adaptation │  │
│  │              │  │   Manager    │  │     Log      │  │   Engine   │  │
│  │ - S4 invoke  │  │              │  │              │  │            │  │
│  │ - S3 invoke  │  │ - Tasks      │  │ - JSONL      │  │ - Metrics  │  │
│  │ - S2 invoke  │  │ - Metrics    │  │ - Events     │  │ - Triggers │  │
│  │ - S1 execute │  │ - Registry   │  │ - Queries    │  │ - Actions  │  │
│  │ - S3* audit  │  │ - Allocation │  │              │  │            │  │
│  │ - S5 resolve │  │              │  │              │  │            │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘  │
│                           │                                             │
│  ┌────────────────────────┴───────────────────────────────────────┐    │
│  │                   Complexity Analyzer                           │    │
│  │  - Keyword patterns    - Domain detection    - Scope estimation │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         State Layer                                      │
│  .claude/vsm-state/                                                     │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────────┐│
│  │ current-task   │  │ viability-     │  │ execution-log.jsonl        ││
│  │ .json          │  │ metrics.json   │  │ (append-only audit trail)  ││
│  └────────────────┘  └────────────────┘  └────────────────────────────┘│
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────────┐│
│  │ agent-registry │  │ s3-allocations │  │ s4-environment.json        ││
│  │ .json          │  │ .json          │  │ (strategic analysis)       ││
│  └────────────────┘  └────────────────┘  └────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

## VSM System Mapping

### System 5 - Policy

**Purpose**: Identity, goals, ultimate authority

**Agent**: `system5-policy`

**Responsibilities**:
- Resolve S3/S4 conflicts
- Set policies for ambiguous situations
- Maintain system coherence

**Invocation**: Only when conflicts detected or policy decisions needed

### System 4 - Intelligence

**Purpose**: Environment scanning, future planning

**Agent**: `system4-strategy`

**Responsibilities**:
- Analyze task in context
- Research external information
- Identify risks and opportunities
- Recommend strategic approach

**Invocation**: Start of every VSM cycle

### System 3 - Control

**Purpose**: Resource allocation, optimization

**Agent**: `system3-control`

**Responsibilities**:
- Assess task complexity
- Select appropriate S1 agents
- Allocate resources
- Monitor S1 performance

**Invocation**: After S4 analysis

### System 3* - Audit

**Purpose**: Quality verification

**Agent**: `system3-audit`

**Responsibilities**:
- Verify work quality
- Check completeness
- Detect oscillation
- Report metrics

**Invocation**: After S1 completion

### System 2 - Coordination

**Purpose**: Anti-oscillation, scheduling

**Agent**: `system2-coordination`

**Responsibilities**:
- Create execution schedules
- Prevent resource conflicts
- Define handoff protocols
- Dampen disturbances

**Invocation**: After S3 allocation

### System 1 - Operations

**Purpose**: Task execution

**Agents**:
- Generalist: `s1-generalist-coder`
- Functional: `s1-code-writer`, `s1-tester`, `s1-reviewer`, `s1-documenter`
- Domain: `s1-frontend`, `s1-backend`, `s1-database`, `s1-infrastructure`

**Invocation**: According to S2 schedule

## Control Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                         VSM Cycle                                │
│                                                                  │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐      │
│  │   S4    │───▶│   S3    │───▶│   S2    │───▶│   S1    │      │
│  │Strategy │    │Control  │    │  Coord  │    │  Ops    │      │
│  └─────────┘    └────┬────┘    └─────────┘    └────┬────┘      │
│                      │                              │            │
│                      │     ┌─────────┐              │            │
│                      │     │   S5    │◀─────────────┤            │
│                      │     │ Policy  │  (conflicts) │            │
│                      │     └─────────┘              │            │
│                      │                              │            │
│                      │         ┌─────────┐          │            │
│                      └────────▶│   S3*   │◀─────────┘            │
│                                │  Audit  │                       │
│                                └────┬────┘                       │
│                                     │                            │
│                                     ▼                            │
│                              ┌─────────────┐                     │
│                              │   Metrics   │                     │
│                              │   Update    │                     │
│                              └─────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

## Complexity Analysis

The complexity analyzer uses multiple signals:

### Keyword Patterns

```python
SIMPLE = ["fix typo", "rename", "minor", "small change"]
MEDIUM = ["add feature", "implement", "fix bug", "test"]
COMPLEX = ["refactor", "architect", "migrate", "security"]
```

### Domain Detection

```python
DOMAINS = {
    "frontend": ["react", "css", "ui", "component"],
    "backend": ["api", "endpoint", "service", "auth"],
    "database": ["sql", "migration", "schema", "query"],
    "infrastructure": ["docker", "kubernetes", "deploy", "ci/cd"]
}
```

### Scoring

```
Final Complexity = weighted(keyword_score, domain_count, scope_estimate)
                 + threshold_adjustment  # from adaptations
```

## Adaptation System

### Triggers and Actions

| Trigger | Condition | Action |
|---------|-----------|--------|
| Agent errors | `error_rate > 0.3` | Add review step |
| Low completion | `completion_rate < 0.5` | Lower complexity threshold |
| Oscillation | `oscillation_rate > 0.2` | Increase S2 involvement |
| Policy conflicts | `s3_s4_conflicts > 3` | Require S5 approval |
| Slow execution | `avg_iterations > 1.5` | Parallelize S1 agents |
| Audit failures | `audit_pass_rate < 0.8` | Tighten S3* audits |

### Metric Updates

Metrics use exponential moving average:

```python
new_rate = alpha * current_value + (1 - alpha) * old_rate
# alpha = 0.1-0.2 for gradual adaptation
```

## State Schema

### current-task.json

```json
{
  "id": "a1b2c3d4",
  "description": "Task description",
  "created_at": "2024-01-15T10:30:00Z",
  "status": "in_progress",
  "complexity": "medium",
  "assigned_agents": ["code-writer", "tester"],
  "metadata": {}
}
```

### viability-metrics.json

```json
{
  "window": "last_10_tasks",
  "completion_rate": 0.85,
  "agent_errors": {
    "code-writer": 0.05,
    "tester": 0.15
  },
  "oscillation_rate": 0.08,
  "audit_pass_rate": 0.92,
  "s3_s4_conflicts": 2,
  "avg_cycle_iterations": 1.3,
  "active_adaptations": [
    {
      "type": "add_review_step",
      "trigger": "tester_errors",
      "applied": "2024-01-15"
    }
  ],
  "last_updated": "2024-01-15T10:30:00Z"
}
```

### execution-log.jsonl

```json
{"timestamp": "...", "event_type": "task_started", "task_id": "...", "data": {...}}
{"timestamp": "...", "event_type": "agent_invoked", "agent": "s1-code-writer", ...}
{"timestamp": "...", "event_type": "agent_completed", "agent": "s1-code-writer", ...}
{"timestamp": "...", "event_type": "audit_performed", "passed": true, ...}
{"timestamp": "...", "event_type": "task_completed", "success": true, ...}
```

## Hook System

### PostToolUse

Logs every tool invocation for audit trail:

```json
{
  "matcher": "*",
  "hooks": [{
    "type": "command",
    "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/log_action.py"
  }]
}
```

### SubagentStop

Updates metrics when agents complete:

```json
{
  "matcher": "s1-*",
  "hooks": [{
    "type": "command",
    "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/update_metrics.py"
  }]
}
```

## Extension Points

### Adding New S1 Agents

1. Create `agents/system1/<agent-name>.md`
2. Follow the existing agent template
3. Add to `plugin.json` agents list
4. Update `agent-registry.json` default

### Custom Complexity Rules

Modify `complexity_analyzer.py`:

```python
# Add new keywords
COMPLEXITY_KEYWORDS[Complexity.COMPLEX].append(r"\bml\b")

# Add new domain
DOMAIN_PATTERNS["ml"] = [r"\bmodel\b", r"\btraining\b", r"\binference\b"]
```

### Custom Adaptations

Extend `adaptation.py`:

```python
class AdaptationType(str, Enum):
    # ... existing types
    CUSTOM_ACTION = "custom_action"

def analyze_metrics(self, metrics):
    # ... existing checks
    if custom_condition:
        adaptations.append(Adaptation(
            type=AdaptationType.CUSTOM_ACTION,
            trigger="custom_trigger",
            effect="Custom effect description"
        ))
```

## Performance Considerations

### Agent Invocation

Each agent invocation starts a new Claude session. Minimize unnecessary invocations:

- S4 analysis should be thorough but not excessive
- S3 should avoid over-allocating agents
- S2 should batch work where possible

### State I/O

State files are read/written frequently. Keep them small:

- Execution log is append-only (grows over time)
- Consider periodic log rotation for long-running projects
- Metrics file stays small (fixed structure)

### Parallelization

S1 agents can run in parallel when:

- Working on different files
- No shared dependencies
- S2 indicates parallel is safe

Enable via adaptation or explicit configuration.
