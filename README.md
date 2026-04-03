# VSM Agent Orchestration

A Claude Code skill for orchestrating development tasks using structural insights from Stafford Beer's Viable Systems Model.

## What This Is

Not a framework. Not a pipeline. A single skill (`/vsm`) that makes three decisions about when to externalize regulatory functions to separate agents:

1. **Scout** (S4 — Intelligence): Spawn a separate agent to survey the codebase before the implementer starts. Prevents the implementer from inheriting a narrow view of the landscape.

2. **Audit** (S3* — Sporadic Audit): Spawn a separate agent to review the implementation blind — given only the goal and the diff, not the implementer's reasoning. Prevents confirmation bias.

3. **Coordination** (S2 — Anti-oscillation): When parallelizing work across agents, define explicit file ownership and interface contracts. Prevents collisions.

Each externalization is independently applied or skipped based on the task. Simple tasks get none. Complex tasks might get all three.

## Why This Approach

The original version of this repo had a Python orchestrator, 14 agent definitions, hooks, state files, and a plugin system. It treated VSM as a sequential pipeline (S4→S3→S2→S1→S3*→S5), which missed the core insight.

Beer's model isn't about phases — it's about concurrent regulatory concerns. The key insight is that certain functions are **structurally compromised** when performed by the same agent that does the work:

- You can't scout objectively when you've already started implementing
- You can't audit your own work — confirmation bias is structural, not a character flaw
- Parallel agents can't coordinate without explicit signals

Claude Code now has native subagents, hooks, and skills. The infrastructure is built in. What's useful is knowing **when and why** to externalize, not building a framework to do it.

## Usage

```
/vsm "Implement user authentication with OAuth"
```

The skill guides Claude through three binary decisions and applies the appropriate externalizations.

## References

- [Stafford Beer's Viable Systems Model](https://en.wikipedia.org/wiki/Viable_system_model)

## License

MIT
