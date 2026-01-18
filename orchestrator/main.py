#!/usr/bin/env python3
"""
VSM Orchestrator Main Entry Point

Command-line interface for running VSM-orchestrated development tasks.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

from .vsm_loop import VSMLoop, VSMCycleResult
from .state_manager import StateManager
from .execution_log import ExecutionLog


def print_result(result: VSMCycleResult, verbose: bool = False) -> None:
    """Print the result of a VSM cycle."""
    status = "SUCCESS" if result.success else "FAILED"
    print(f"\n{'='*60}")
    print(f"VSM Cycle Complete: {status}")
    print(f"{'='*60}")
    print(f"Task ID: {result.task_id}")
    print(f"Summary: {result.summary}")

    if result.agents_invoked:
        print(f"\nAgents Invoked:")
        for agent in result.agents_invoked:
            print(f"  - {agent}")

    if result.audit_passed is not None:
        audit_status = "PASSED" if result.audit_passed else "FAILED"
        print(f"\nAudit: {audit_status}")

    if result.conflicts:
        print(f"\nConflicts Detected: {len(result.conflicts)}")
        for conflict in result.conflicts:
            print(f"  - {conflict.get('type', 'unknown')}")

    if result.adaptations:
        print(f"\nAdaptations Applied: {len(result.adaptations)}")
        for adaptation in result.adaptations:
            print(f"  - {adaptation.get('type', 'unknown')}: {adaptation.get('effect', '')}")

    if verbose and result.s1_results:
        print(f"\nDetailed Agent Results:")
        for agent_result in result.s1_results:
            status = "OK" if agent_result.success else "FAILED"
            print(f"\n  [{status}] {agent_result.agent}")
            if agent_result.output:
                # Truncate long output
                output = agent_result.output[:500]
                if len(agent_result.output) > 500:
                    output += "..."
                print(f"    Output: {output}")
            if agent_result.error:
                print(f"    Error: {agent_result.error}")

    print(f"\n{'='*60}\n")


def print_state(state_manager: StateManager) -> None:
    """Print current VSM state."""
    print("\n" + "="*60)
    print("VSM State")
    print("="*60)

    # Current task
    task = state_manager.get_current_task()
    if task:
        print(f"\nCurrent Task:")
        print(f"  ID: {task.id}")
        print(f"  Description: {task.description[:100]}...")
        print(f"  Status: {task.status}")
        print(f"  Complexity: {task.complexity}")
    else:
        print("\nNo active task")

    # Viability metrics
    metrics = state_manager.get_viability_metrics()
    print(f"\nViability Metrics:")
    print(f"  Completion Rate: {metrics.completion_rate:.2%}")
    print(f"  Audit Pass Rate: {metrics.audit_pass_rate:.2%}")
    print(f"  Oscillation Rate: {metrics.oscillation_rate:.2%}")
    print(f"  S3/S4 Conflicts: {metrics.s3_s4_conflicts}")

    if metrics.agent_errors:
        print(f"\n  Agent Error Rates:")
        for agent, rate in metrics.agent_errors.items():
            print(f"    {agent}: {rate:.2%}")

    if metrics.active_adaptations:
        print(f"\n  Active Adaptations:")
        for adaptation in metrics.active_adaptations:
            print(f"    - {adaptation.get('type')}: {adaptation.get('effect')}")

    # Agent registry
    registry = state_manager.get_agent_registry()
    print(f"\nAgent Registry:")
    for name, info in registry.get("agents", {}).items():
        status = info.get("status", "unknown")
        agent_type = info.get("type", "unknown")
        print(f"  {name} ({agent_type}): {status}")

    print("\n" + "="*60 + "\n")


def print_log(log: ExecutionLog, count: int = 20) -> None:
    """Print recent execution log entries."""
    print("\n" + "="*60)
    print("Execution Log (Recent)")
    print("="*60 + "\n")

    entries = log.read_recent(count)
    if not entries:
        print("No log entries found.")
        return

    for entry in entries:
        timestamp = entry.timestamp[:19]  # Trim microseconds
        event = entry.event_type
        agent = entry.agent or "-"
        task = entry.task_id[:8] if entry.task_id else "-"
        print(f"[{timestamp}] {event:20} | Agent: {agent:20} | Task: {task}")

    print("\n" + "="*60 + "\n")


async def run_task(task: str, working_dir: Optional[Path] = None,
                   complexity_hint: Optional[str] = None,
                   verbose: bool = False) -> int:
    """Run a VSM-orchestrated task."""
    loop = VSMLoop(working_dir=working_dir)

    print(f"\nStarting VSM cycle for task:")
    print(f"  {task[:100]}{'...' if len(task) > 100 else ''}")
    if complexity_hint:
        print(f"  Complexity hint: {complexity_hint}")
    print()

    try:
        result = await loop.run_cycle(task, complexity_hint=complexity_hint)
        print_result(result, verbose=verbose)
        return 0 if result.success else 1
    except Exception as e:
        print(f"\nError during VSM cycle: {e}")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="VSM Multi-Agent Orchestrator for Development Tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a task
  python -m orchestrator "Add a user authentication feature"

  # Run with complexity hint
  python -m orchestrator "Fix typo in README" --simple

  # View current state
  python -m orchestrator --state

  # View execution log
  python -m orchestrator --log

  # Reset state
  python -m orchestrator --reset
"""
    )

    parser.add_argument("task", nargs="?", help="The task to execute")
    parser.add_argument("-d", "--dir", type=Path, help="Working directory")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Verbose output")
    parser.add_argument("--simple", action="store_true",
                       help="Hint that task is simple")
    parser.add_argument("--medium", action="store_true",
                       help="Hint that task is medium complexity")
    parser.add_argument("--complex", action="store_true",
                       help="Hint that task is complex")
    parser.add_argument("--state", action="store_true",
                       help="Show current VSM state")
    parser.add_argument("--log", action="store_true",
                       help="Show execution log")
    parser.add_argument("--log-count", type=int, default=20,
                       help="Number of log entries to show")
    parser.add_argument("--reset", action="store_true",
                       help="Reset VSM state")
    parser.add_argument("--json", action="store_true",
                       help="Output in JSON format")

    args = parser.parse_args()

    # Determine complexity hint
    complexity_hint = None
    if args.simple:
        complexity_hint = "simple"
    elif args.medium:
        complexity_hint = "medium"
    elif args.complex:
        complexity_hint = "complex"

    # Handle state commands
    state_manager = StateManager()

    if args.reset:
        state_manager.reset_state()
        print("VSM state has been reset.")
        return 0

    if args.state:
        if args.json:
            print(json.dumps(state_manager.get_all_state(), indent=2, default=str))
        else:
            print_state(state_manager)
        return 0

    if args.log:
        log = ExecutionLog()
        if args.json:
            entries = log.read_recent(args.log_count)
            print(json.dumps([e.__dict__ for e in entries], indent=2))
        else:
            print_log(log, args.log_count)
        return 0

    # Run task
    if not args.task:
        parser.print_help()
        return 1

    return asyncio.run(run_task(
        args.task,
        working_dir=args.dir,
        complexity_hint=complexity_hint,
        verbose=args.verbose
    ))


if __name__ == "__main__":
    sys.exit(main())
