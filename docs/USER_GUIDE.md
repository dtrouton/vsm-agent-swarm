# VSM Orchestrator User Guide

This guide walks you through using the VSM Multi-Agent Orchestrator for your development tasks.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Your First VSM Task](#your-first-vsm-task)
3. [Understanding the Output](#understanding-the-output)
4. [Working with Different Task Types](#working-with-different-task-types)
5. [Monitoring System Health](#monitoring-system-health)
6. [Advanced Usage](#advanced-usage)
7. [Best Practices](#best-practices)

---

## Getting Started

### Prerequisites

- Claude Code CLI installed and configured
- Python 3.8+ (for the orchestrator)

### Installation

Link the plugin to your Claude Code plugins directory:

```bash
ln -s /path/to/vsm-orchestrator ~/.claude/plugins/vsm-orchestrator
```

Verify installation:

```bash
# Should show vsm-orchestrator in the list
claude /plugins
```

### First Run

The VSM system creates its state directory on first use:

```bash
/vsm "Say hello"
```

This creates `.claude/vsm-state/` in your working directory.

---

## Your First VSM Task

### Simple Example

Let's start with a simple task:

```bash
/vsm "Add a greeting function to utils.js"
```

The system will:

1. **Analyze** - S4 examines your codebase and the task
2. **Allocate** - S3 determines this is a simple task → Generalist Coder
3. **Coordinate** - S2 creates a simple execution plan
4. **Execute** - The generalist agent adds the function
5. **Audit** - S3* verifies the code quality

### What You'll See

```
Starting VSM cycle for task:
  Add a greeting function to utils.js

[S4] Analyzing task and environment...
[S3] Allocating resources: simple complexity → generalist-coder
[S2] Creating execution schedule...
[S1] Executing: generalist-coder
[S3*] Auditing results...

============================================================
VSM Cycle Complete: SUCCESS
============================================================
Task ID: a1b2c3d4
Summary: Completed with 1/1 agents successful. Audit passed.

Agents Invoked:
  - s1-generalist-coder

Audit: PASSED
============================================================
```

---

## Understanding the Output

### Cycle Status

- **SUCCESS** - Task completed, audit passed
- **FAILED** - Task failed or audit found issues

### Agent Results

Each S1 agent reports:
- Files modified
- Changes made
- Any blockers encountered

### Audit Results

S3* checks for:
- Code quality
- Completeness
- Style consistency
- Potential issues

### Adaptations

If the system applied automatic adaptations, they're listed:

```
Adaptations Applied: 1
  - add_review_step: Add reviewer before tester
```

---

## Working with Different Task Types

### Simple Tasks

Best for: Typo fixes, comment updates, small tweaks

```bash
/vsm "Fix the typo in README.md"
/vsm "Rename the 'usr' variable to 'user'"
/vsm --complexity=simple "Add a TODO comment"
```

**Agent used**: `s1-generalist-coder`

### Medium Tasks

Best for: New features, bug fixes, test additions

```bash
/vsm "Add input validation to the login form"
/vsm "Create unit tests for the UserService class"
/vsm "Fix the pagination bug in the product list"
```

**Agents used**: `s1-code-writer`, `s1-tester`, `s1-reviewer`

### Complex Tasks

Best for: Architecture changes, multi-domain features, migrations

```bash
/vsm "Implement OAuth2 authentication"
/vsm "Add real-time notifications using WebSockets"
/vsm --complexity=complex "Migrate from REST to GraphQL"
```

**Agents used**: Domain specialists based on task requirements

### Specifying Complexity

Override automatic detection when you know better:

```bash
# Force simple (single agent, fast)
/vsm --complexity=simple "Quick database fix"

# Force medium (functional specialists)
/vsm --complexity=medium "Add caching layer"

# Force complex (domain specialists)
/vsm --complexity=complex "Redesign the API"
```

---

## Monitoring System Health

### View Current State

```bash
python -m orchestrator --state
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
  Complexity: complex

Viability Metrics:
  Completion Rate: 85.00%
  Audit Pass Rate: 92.00%
  Oscillation Rate: 8.00%
  S3/S4 Conflicts: 2

  Agent Error Rates:
    code-writer: 5.00%
    tester: 15.00%
    reviewer: 3.00%

  Active Adaptations:
    - add_review_step: Add reviewer before tester
============================================================
```

### View Execution Log

```bash
# Last 20 entries
python -m orchestrator --log

# Last 50 entries
python -m orchestrator --log --log-count=50
```

### JSON Output

For programmatic access:

```bash
python -m orchestrator --state --json
python -m orchestrator --log --json
```

### Understanding Metrics

| Metric | Good | Warning | Action Needed |
|--------|------|---------|---------------|
| Completion Rate | > 85% | 70-85% | < 70% |
| Audit Pass Rate | > 90% | 80-90% | < 80% |
| Oscillation Rate | < 10% | 10-20% | > 20% |
| Agent Errors | < 15% | 15-30% | > 30% |

---

## Advanced Usage

### Direct Agent Invocation

Skip the VSM loop and invoke agents directly:

```bash
# Strategic analysis only
claude --agent system4-strategy "Analyze the payment module architecture"

# Code review only
claude --agent s1-reviewer "Review the changes in src/auth/"

# Frontend work only
claude --agent s1-frontend "Create a responsive navbar component"
```

### Viewing Agent Definitions

Read agent prompts to understand their capabilities:

```bash
cat ~/.claude/plugins/vsm-orchestrator/agents/s1-frontend.md
```

### Resetting State

Start fresh if state becomes corrupted:

```bash
python -m orchestrator --reset
```

### Running from Different Directory

```bash
python -m orchestrator -d /path/to/project "Task description"
```

---

## Best Practices

### 1. Write Clear Task Descriptions

**Good:**
```
/vsm "Add email validation to the registration form that checks for valid format and displays an error message"
```

**Not as good:**
```
/vsm "Fix the form"
```

### 2. Use Complexity Hints When Confident

If you know a task is simple, say so:

```bash
/vsm --complexity=simple "Update the copyright year"
```

This saves time by skipping unnecessary analysis.

### 3. Check State After Complex Tasks

```bash
python -m orchestrator --state
```

Ensure metrics are healthy and no adaptations are running unnecessarily.

### 4. Review Audit Findings

Even on success, audit might note improvements:

```
Audit: PASSED
Quality: acceptable
Notes: Consider adding error handling for edge cases
```

### 5. Let the System Learn

Don't reset state frequently. The system learns from history:
- Agent error rates inform future allocation
- Oscillation detection prevents repeated mistakes
- Conflict patterns improve policy decisions

### 6. Break Large Tasks Down

Instead of:
```bash
/vsm "Build the entire user management system"
```

Consider:
```bash
/vsm "Create the User model and database schema"
/vsm "Implement user CRUD API endpoints"
/vsm "Add user authentication middleware"
/vsm "Create user management UI components"
```

### 7. Monitor for Oscillation

If you see oscillation warnings:
- The system will automatically increase S2 coordination
- Consider breaking the task into smaller pieces
- Check if requirements are clear

---

## Troubleshooting

### "Agent selection seems wrong"

Use complexity hints:
```bash
/vsm --complexity=complex "Task needing specialists"
```

### "Task keeps failing"

1. Check the execution log: `python -m orchestrator --log`
2. Look for specific agent errors
3. Try with explicit complexity
4. Consider breaking into smaller tasks

### "Oscillation detected"

The system handles this automatically, but you can:
1. Check which agents are conflicting (in the log)
2. Ensure task requirements are clear
3. Consider manual agent invocation for specific parts

### "State seems corrupted"

```bash
python -m orchestrator --reset
```

---

## Getting Help

- View this guide: `cat docs/USER_GUIDE.md`
- View README: `cat README.md`
- Check agent capabilities: `cat agents/<agent-name>.md`
- View current state: `python -m orchestrator --state`
