---
name: vsm
description: Execute a task using VSM multi-agent orchestration
arguments:
  - name: task
    description: The development task to execute
    required: false
  - name: complexity
    description: Hint about task complexity (simple, medium, complex)
    required: false
---

# VSM Orchestration Command

Execute a development task using the Viable Systems Model multi-agent orchestration.

## Usage

```
/vsm <task description>
/vsm --complexity=simple "Fix typo in README"
/vsm --complexity=complex "Implement user authentication system"
```

## What This Does

This command orchestrates multiple specialized AI agents following Stafford Beer's Viable Systems Model:

1. **S4 (Intelligence)** analyzes the task and environment
2. **S3 (Control)** allocates appropriate agents based on complexity
3. **S2 (Coordination)** schedules work to prevent conflicts
4. **S1 (Operations)** executes the task with specialized agents
5. **S3* (Audit)** verifies the quality of work
6. **S5 (Policy)** resolves any conflicts if needed

## Agent Selection

Based on task complexity:

- **Simple**: Generalist Coder (single agent)
- **Medium**: Functional Specialists (Code Writer, Tester, Reviewer, Documenter)
- **Complex**: Domain Specialists (Frontend, Backend, Database, Infrastructure)

## Instructions

When this command is invoked:

1. If a task is provided as an argument, use that as the task description
2. If no task is provided, ask the user what task they want to execute
3. Read any existing VSM state from `.claude/vsm-state/`
4. Execute the VSM loop by invoking agents in sequence:
   - First invoke `system4-strategy` to analyze the task
   - Then invoke `system3-control` to determine resource allocation
   - Then invoke `system2-coordination` to create an execution plan
   - Then invoke the selected S1 agents based on allocation
   - Finally invoke `system3-audit` to verify results
5. Handle any conflicts by invoking `system5-policy` if needed
6. Report the results to the user

## Arguments

- `task`: The development task to execute (optional - will prompt if not provided)
- `complexity`: Hint about task complexity to guide agent selection (optional)
  - `simple`: Use generalist coder for quick fixes
  - `medium`: Use functional specialists for feature development
  - `complex`: Use domain specialists for architectural changes

## State Files

The VSM system maintains state in `.claude/vsm-state/`:
- `current-task.json`: Active task details
- `viability-metrics.json`: System health metrics
- `agent-registry.json`: Available agents and status
- `execution-log.jsonl`: Audit trail
- `s3-allocations.json`: Resource allocation decisions
- `s4-environment.json`: Strategic analysis
