---
name: vsm
description: Orchestrate a development task using structural externalizations from the Viable Systems Model — scout, audit, and coordination.
---

# VSM Task Orchestration

You have been asked to complete a development task using VSM-informed orchestration.

The core idea: certain regulatory functions are structurally compromised when performed by the same agent that does the work. VSM identifies three functions worth externalizing to separate agents. Each is independently justified or skipped based on the task.

## The Three Externalizations

### 1. Scout (externalized S4 — Intelligence)

**What**: A separate agent surveys the landscape before implementation begins.

**Why it's structural**: The implementing agent reads the files it will edit and inherits their worldview. A scout looks at the surrounding context — adjacent modules, test patterns, conventions, recent changes — and forms an approach recommendation that the implementer receives as input rather than discovering piecemeal.

**When to use**:
- The approach is uncertain (multiple valid paths, unclear which is right)
- The task touches unfamiliar or sprawling parts of the codebase
- The codebase has non-obvious conventions a naive implementer would violate
- Getting the approach wrong would be expensive to reverse

**When to skip**:
- The task is well-understood with an obvious approach
- The change is localized to a single file or function
- You already know the relevant patterns

**What the scout produces**: A brief for the implementer — "here's the pattern used elsewhere, here are the files that will be affected, here's the approach and why, here's the risk." Keep it short. The scout's job is to prevent the implementer from making an uninformed architectural choice, not to write a design doc.

**How to run it**: Spawn an Agent (subagent_type: Explore) with thorough exploration. Give it the task description and ask it to research the codebase and recommend an approach. Do NOT ask it to implement anything.

---

### 2. Audit (externalized S3* — Sporadic Audit)

**What**: A separate agent reviews the implementation with fresh eyes.

**Why it's structural**: Confirmation bias isn't a character flaw — it's a structural property of self-review. The agent that wrote the code already "knows" why every decision was made. Beer's S3* exists precisely because normal reporting channels are biased. The audit bypasses them.

**When to use**:
- Almost always for non-trivial changes
- Changes that affect control flow, security, data integrity
- Multi-file changes where interactions matter

**When to skip**:
- Truly mechanical changes (rename, formatting) where correctness is obvious
- Single-line fixes with no ambiguity

**What the auditor gets**:
- The original task description (what was asked for)
- The diff (what changed)
- Access to read the codebase
- **NOT** the implementer's reasoning or plan — this is critical. If you feed it the plan, it becomes a rubber stamp.

**What the auditor does**: Independently assesses whether the diff achieves the goal correctly. Looks for: missed edge cases, broken assumptions, convention violations, unintended side effects, security issues.

**How to run it**: After implementation, spawn an Agent with a prompt like: "Here is a task that was requested: [task]. Here is what was changed: [diff or file list]. Review the changes. Do they correctly and completely achieve the goal? What problems do you see? Be specific." Give it read access. Do NOT tell it what approach was taken or why.

---

### 3. Coordination (externalized S2 — Anti-oscillation)

**What**: Explicit constraints given to parallel agents so they don't collide.

**Why it's structural**: When you spawn multiple agents, they can't see each other. Without explicit boundaries, they may edit the same files, create inconsistent interfaces, duplicate work, or make contradictory architectural choices. S2 in Beer's model isn't a decision-maker — it's a signaling mechanism. Think traffic lights, not a traffic cop.

**When to use**:
- Spawning 2+ agents that will work on the same codebase
- Agents whose outputs must compose (e.g., API + frontend, schema + migration)

**When to skip**:
- Single agent doing sequential work
- Parallel agents touching completely disjoint parts of the system

**What coordination looks like**:
- **File ownership**: "You own `src/api/`. Do not modify anything outside it."
- **Interface contracts**: "The function signature must be `processOrder(order: Order): Result`. Agent B depends on this."
- **Shared context**: Both agents receive the same scout brief so they share architectural assumptions.
- **Sequencing**: If Agent B depends on Agent A's output, don't parallelize — run A first.

**How to do it**: Before spawning parallel agents, define the boundaries in each agent's prompt. Be explicit about what each agent owns and what interfaces they must respect.

---

## Execution Flow

Given the task, make three binary decisions:

```
1. Is the approach uncertain or the codebase unfamiliar?
   YES → Spawn scout. Feed its brief to the implementer(s).
   NO  → Skip to implementation.

2. Can the work be meaningfully parallelized?
   YES → Define file ownership + interface contracts. Launch parallel agents.
   NO  → Single agent implements.

3. Is the change non-trivial?
   YES → Spawn auditor with (original task + diff). No implementer reasoning.
   NO  → Skip audit.
```

These are independent decisions, not a pipeline. A task might get scout + audit but no parallelization. Another might get parallelization + coordination but no scout.

## Important Principles

- **Don't add ceremony for its own sake.** If a task is simple, just do it. The value of externalization is structural separation of concerns — if there's nothing to separate, don't.

- **The auditor must be blind to the plan.** This is the single most important rule. An auditor who knows the implementer's reasoning will confirm it. An auditor who only sees the goal and the diff will challenge it.

- **Coordination is constraints, not a coordinator.** Don't spawn a "coordination agent." Define boundaries in the prompts of the agents doing the work.

- **The scout's job is to prevent bad starts, not to plan everything.** A 200-word brief is better than a 2000-word design doc. The implementer still makes tactical decisions.

- **Recursion is implicit.** Each subagent naturally orients before acting if prompted well. You don't need to tell subagents to "follow VSM." The structural externalizations happen at the level where you're spawning agents — that's where the architectural decisions live.
