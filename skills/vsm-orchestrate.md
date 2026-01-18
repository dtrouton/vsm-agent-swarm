---
name: vsm-orchestrate
description: Use this skill to orchestrate development tasks using the Viable Systems Model multi-agent architecture
---

# VSM Orchestration Skill

This skill enables VSM (Viable Systems Model) multi-agent orchestration for development tasks.

## Overview

The VSM architecture coordinates multiple specialized AI agents to complete development tasks effectively. It's based on Stafford Beer's Viable Systems Model, which ensures system viability through proper coordination and control.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  SYSTEM 5 (Policy)                                              │
│  PolicyAgent: Maintains goals, identity, resolves S3/S4 conflict│
└─────────────────────────────────────────────────────────────────┘
        ↕ balances
┌─────────────────────────────────────────────────────────────────┐
│  SYSTEM 4 (Intelligence)      │  SYSTEM 3 (Control)            │
│  StrategyAgent: Environment   │  ControlAgent: Resource alloc, │
│  scanning, future planning    │  optimization, monitors S1     │
└───────────────────────────────┴─────────────────────────────────┘
                                        ↕ manages
┌─────────────────────────────────────────────────────────────────┐
│  SYSTEM 3* (Audit)                                              │
│  AuditAgent: Quality checks, verifies actual vs reported        │
└─────────────────────────────────────────────────────────────────┘
                                        ↕ audits
┌─────────────────────────────────────────────────────────────────┐
│  SYSTEM 2 (Coordination)                                        │
│  CoordinationAgent: Schedules work, prevents conflicts          │
└─────────────────────────────────────────────────────────────────┘
                                        ↕ coordinates
┌─────────────────────────────────────────────────────────────────┐
│  SYSTEM 1 (Operations) - Graduated Pool                         │
│  Generalist │ Functional Specialists │ Domain Specialists       │
└─────────────────────────────────────────────────────────────────┘
```

## How to Use This Skill

### Step 1: Understand the Task

When the user provides a development task, first analyze it to understand:
- What needs to be done
- What files might be involved
- What the expected outcome is

### Step 2: Run the VSM Loop

Execute the VSM loop in this order:

1. **Invoke S4 (Strategy Agent)**
   ```
   Task the system4-strategy agent with analyzing the task and environment.
   It will research, explore the codebase, and provide strategic recommendations.
   ```

2. **Invoke S3 (Control Agent)**
   ```
   Task the system3-control agent with determining resource allocation.
   Based on S4's analysis, it decides which S1 agents to use.
   ```

3. **Invoke S2 (Coordination Agent)**
   ```
   Task the system2-coordination agent with creating an execution schedule.
   It prevents conflicts between agents working on the same resources.
   ```

4. **Execute S1 Agents**
   ```
   Invoke the selected S1 agents in the order specified by S2.
   Monitor their progress and handle any issues.
   ```

5. **Invoke S3* (Audit Agent)**
   ```
   Task the system3-audit agent with verifying the completed work.
   It checks quality, completeness, and detects any oscillation.
   ```

6. **Handle Conflicts (if needed)**
   ```
   If S3 and S4 disagree, invoke system5-policy to resolve.
   ```

### Step 3: Report Results

After the VSM loop completes:
- Summarize what was done
- List files modified
- Report any issues or concerns
- Note audit results

## Agent Reference

### Higher-Level Systems

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| system5-policy | Policy decisions, conflict resolution | S3/S4 conflicts |
| system4-strategy | Strategic analysis, research | Task start |
| system3-control | Resource allocation, complexity assessment | After S4 |
| system3-audit | Quality verification | After S1 complete |
| system2-coordination | Scheduling, conflict prevention | After S3 |

### S1 Operations Agents

| Agent | Type | When to Use |
|-------|------|-------------|
| s1-generalist-coder | Generalist | Simple tasks |
| s1-code-writer | Functional | Feature implementation |
| s1-tester | Functional | Test creation |
| s1-reviewer | Functional | Code review |
| s1-documenter | Functional | Documentation |
| s1-frontend | Domain | UI/UX work |
| s1-backend | Domain | API/service work |
| s1-database | Domain | Schema/query work |
| s1-infrastructure | Domain | DevOps work |

## Complexity Guidelines

### Simple Tasks
- Single file changes
- Clear, atomic requirements
- Use: `s1-generalist-coder`

### Medium Tasks
- Multi-file changes
- Needs testing or review
- Use: `s1-code-writer` + `s1-tester` + `s1-reviewer`

### Complex Tasks
- Cross-cutting concerns
- Multiple domains
- Architectural decisions
- Use: Domain specialists as needed

## State Management

The VSM system maintains state in `.claude/vsm-state/`:

- Read existing state before starting
- Update state as work progresses
- Agents communicate via state files

## Automatic Adaptation

The system self-adjusts based on viability metrics:

- High agent error rate → Add review steps
- Oscillation detected → Increase coordination
- Frequent conflicts → Require S5 approval

Check `.claude/vsm-state/viability-metrics.json` for current adaptations.
