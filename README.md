# VSM Multi-Agent Orchestrator

A Claude Code plugin implementing Stafford Beer's Viable Systems Model (VSM) for coordinating multiple AI agents on development tasks.

## Overview

The VSM Orchestrator coordinates specialized AI agents in a hierarchical control structure that mirrors how viable organizations manage complexity. Instead of a single agent handling everything, tasks are analyzed, allocated, coordinated, executed, and audited by purpose-built agents.

```
┌─────────────────────────────────────────────────────────────────┐
│  S5 (Policy) - Goals, identity, conflict resolution             │
├─────────────────────────────────────────────────────────────────┤
│  S4 (Intelligence)          │  S3 (Control)                    │
│  Environment scanning,      │  Resource allocation,            │
│  research, adaptation       │  optimization                    │
├─────────────────────────────┴───────────────────────────────────┤
│  S3* (Audit) - Quality verification, spot checks               │
├─────────────────────────────────────────────────────────────────┤
│  S2 (Coordination) - Scheduling, conflict prevention           │
├─────────────────────────────────────────────────────────────────┤
│  S1 (Operations) - Generalist │ Functional │ Domain Specialists│
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Installation

1. Clone or copy this plugin to your Claude Code plugins directory:

```bash
# Option 1: Symlink (recommended for development)
ln -s /path/to/vsm-orchestrator ~/.claude/plugins/vsm-orchestrator

# Option 2: Copy
cp -r /path/to/vsm-orchestrator ~/.claude/plugins/
```

2. Verify the plugin is loaded:

```bash
claude /plugins
```

### Basic Usage

Use the `/vsm` command to orchestrate a development task:

```bash
# Simple task
/vsm "Fix the typo in the README"

# With complexity hint
/vsm --complexity=complex "Implement user authentication with OAuth"

# Let the system determine complexity
/vsm "Add pagination to the user list API"
```

## How It Works

### The VSM Cycle

When you invoke `/vsm`, the system runs a complete VSM cycle:

1. **S4 (Intelligence)** analyzes the task
   - Explores the codebase
   - Researches relevant patterns
   - Identifies risks and opportunities
   - Recommends an approach

2. **S3 (Control)** allocates resources
   - Assesses task complexity
   - Selects appropriate S1 agents
   - Considers viability metrics

3. **S2 (Coordination)** creates the execution plan
   - Schedules agent work
   - Prevents file conflicts
   - Defines handoff protocols

4. **S1 (Operations)** executes the task
   - Selected agents work on assigned subtasks
   - Progress tracked via state files

5. **S3* (Audit)** verifies results
   - Checks code quality
   - Verifies completeness
   - Detects oscillation

6. **S5 (Policy)** resolves conflicts (if needed)
   - Balances S3/S4 disagreements
   - Sets policy for edge cases

### Agent Selection

The system automatically selects agents based on task complexity:

| Complexity | Agents Used | Example Tasks |
|------------|-------------|---------------|
| Simple | Generalist Coder | Fix typos, rename variables, add comments |
| Medium | Code Writer, Tester, Reviewer | Add features, fix bugs, update APIs |
| Complex | Domain Specialists + Functional | Architecture changes, new systems, migrations |

### Automatic Adaptation

The system learns from outcomes and adapts:

- **High error rate** for an agent → Adds review step before that agent
- **Oscillation detected** → Increases S2 coordination involvement
- **Frequent S3/S4 conflicts** → Requires S5 approval for allocations
- **Low completion rate** → Lowers complexity thresholds

## State Management

VSM state is stored in `.claude/vsm-state/`:

```
.claude/vsm-state/
├── current-task.json         # Active task
├── viability-metrics.json    # System health
├── agent-registry.json       # Agent status
├── execution-log.jsonl       # Audit trail
├── s3-allocations.json       # Resource decisions
└── s4-environment.json       # Strategic analysis
```

### Viewing State

```bash
# View current state
python -m orchestrator --state

# View execution log
python -m orchestrator --log

# Reset all state
python -m orchestrator --reset
```

## Agent Reference

### System Agents (S2-S5)

| Agent | Role | Invoked When |
|-------|------|--------------|
| `system5-policy` | Policy decisions | S3/S4 conflicts |
| `system4-strategy` | Strategic analysis | Task start |
| `system3-control` | Resource allocation | After S4 |
| `system3-audit` | Quality verification | After S1 |
| `system2-coordination` | Scheduling | After S3 |

### Operational Agents (S1)

#### Generalist
| Agent | Capabilities |
|-------|--------------|
| `s1-generalist-coder` | General coding, simple fixes, small features |

#### Functional Specialists
| Agent | Capabilities |
|-------|--------------|
| `s1-code-writer` | Implementation, new features, code generation |
| `s1-tester` | Unit tests, integration tests, coverage |
| `s1-reviewer` | Code review, best practices, security |
| `s1-documenter` | Documentation, API docs, comments |

#### Domain Specialists
| Agent | Capabilities |
|-------|--------------|
| `s1-frontend` | UI/UX, React/Vue, CSS, accessibility |
| `s1-backend` | APIs, services, authentication |
| `s1-database` | SQL, migrations, data modeling |
| `s1-infrastructure` | DevOps, CI/CD, containers |

## Configuration

### Complexity Hints

Override automatic complexity detection:

```bash
/vsm --complexity=simple "Quick fix"
/vsm --complexity=medium "New feature"
/vsm --complexity=complex "System redesign"
```

### Direct Agent Invocation

You can invoke agents directly via Claude Code:

```bash
claude --agent system4-strategy "Analyze the authentication module"
claude --agent s1-frontend "Create a login form component"
```

## Viability Metrics

The system tracks health metrics:

| Metric | Description | Healthy Range |
|--------|-------------|---------------|
| `completion_rate` | Tasks completed successfully | > 0.8 |
| `audit_pass_rate` | Audits passed | > 0.9 |
| `oscillation_rate` | Changes reverted | < 0.1 |
| `agent_errors` | Per-agent error rates | < 0.2 each |
| `s3_s4_conflicts` | Strategy/control disagreements | < 3 |

## Troubleshooting

### Task Not Completing

1. Check viability metrics: `python -m orchestrator --state`
2. Review execution log: `python -m orchestrator --log`
3. Look for blocked agents or oscillation patterns

### Wrong Agent Selected

Use complexity hints to guide selection:
```bash
/vsm --complexity=complex "Task that needs specialists"
```

### State Corruption

Reset and start fresh:
```bash
python -m orchestrator --reset
```

## Architecture

```
vsm-orchestrator/
├── plugin.json              # Plugin manifest
├── agents/                  # Agent definitions
│   ├── system5-policy.md
│   ├── system4-strategy.md
│   ├── system3-control.md
│   ├── system3-audit.md
│   ├── system2-coordination.md
│   └── system1/            # Operational agents
├── hooks/                   # Observability hooks
├── skills/                  # VSM skill documentation
├── commands/                # /vsm command
├── state/                   # State file templates
└── orchestrator/            # Python orchestrator
    ├── main.py             # CLI entry point
    ├── vsm_loop.py         # Control loop
    ├── state_manager.py    # State persistence
    ├── execution_log.py    # Logging
    ├── complexity_analyzer.py
    └── adaptation.py       # Auto-adaptation
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests (when available)
5. Submit a pull request

## License

MIT License - See LICENSE file for details.

## References

- [Stafford Beer's Viable Systems Model](https://en.wikipedia.org/wiki/Viable_system_model)
- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
