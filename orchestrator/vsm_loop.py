"""
VSM Control Loop

Implements the Viable Systems Model control loop for orchestrating agents.
"""

import asyncio
import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .state_manager import (
    StateManager, CurrentTask, S3Allocation, S4Environment, ViabilityMetrics
)
from .execution_log import ExecutionLog, LogEventType
from .complexity_analyzer import ComplexityAnalyzer, Complexity
from .adaptation import AdaptationEngine


@dataclass
class AgentResult:
    """Result from an agent invocation."""
    agent: str
    success: bool
    output: str
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class VSMCycleResult:
    """Result of a complete VSM cycle."""
    task_id: str
    success: bool
    summary: str
    agents_invoked: List[str]
    audit_passed: Optional[bool] = None
    conflicts: List[dict] = field(default_factory=list)
    adaptations: List[dict] = field(default_factory=list)
    s1_results: List[AgentResult] = field(default_factory=list)


class VSMLoop:
    """
    Implements the VSM control loop.

    The loop follows these phases:
    1. S4 (Intelligence) analyzes the task
    2. S3 (Control) allocates resources
    3. S2 (Coordination) creates execution plan
    4. S1 (Operations) execute the task
    5. S3* (Audit) verifies results
    6. S5 (Policy) resolves conflicts if needed
    """

    def __init__(self, working_dir: Optional[Path] = None,
                 claude_command: str = "claude"):
        """
        Initialize the VSM loop.

        Args:
            working_dir: Working directory for the task
            claude_command: Command to invoke Claude Code CLI
        """
        self.working_dir = working_dir or Path.cwd()
        self.claude_command = claude_command
        self.state = StateManager()
        self.log = ExecutionLog()
        self.adaptation = AdaptationEngine(self.state)

    async def run_cycle(self, task: str, task_id: Optional[str] = None,
                       complexity_hint: Optional[str] = None) -> VSMCycleResult:
        """
        Run a complete VSM cycle for a task.

        Args:
            task: The task description
            task_id: Optional task ID (generated if not provided)
            complexity_hint: Optional hint about task complexity

        Returns:
            VSMCycleResult with the outcome
        """
        # Generate task ID if not provided
        if not task_id:
            task_id = self._generate_task_id()

        # Initialize task state
        current_task = CurrentTask(
            id=task_id,
            description=task,
            created_at=datetime.utcnow().isoformat(),
            status="in_progress"
        )
        self.state.set_current_task(current_task)
        self.log.log_task_started(task_id, task)

        try:
            # Check for and apply adaptations
            metrics = self.state.get_viability_metrics()
            adaptations = self.adaptation.analyze_metrics(metrics)
            if adaptations:
                self.adaptation.apply_adaptations(adaptations)
                for a in adaptations:
                    self.log.log_adaptation(a.type.value, a.trigger, a.effect)

            # Phase 1: S4 analyzes environment & task
            s4_result = await self._invoke_s4(task, task_id)

            # Phase 2: S3 determines resource allocation
            s3_result = await self._invoke_s3(task, s4_result, task_id)

            # Check if S5 approval needed (due to adaptation)
            if self.adaptation.should_require_s5_approval():
                s5_approval = await self._invoke_s5_for_approval(
                    task, s4_result, s3_result, task_id
                )
                if not s5_approval:
                    # S5 rejected, need to re-plan
                    s3_result = await self._invoke_s3(task, s4_result, task_id)

            # Phase 3: S2 creates execution plan
            s2_result = await self._invoke_s2(s3_result, task_id)

            # Phase 4: S1 agents execute
            s1_results = await self._execute_s1_agents(
                s2_result, s3_result, task_id
            )

            # Phase 5: S3* audits results
            audit_result = await self._invoke_s3_star(
                task, s1_results, task_id
            )

            # Phase 6: Check for S3/S4 conflicts
            conflicts = self._detect_conflicts(s3_result, s4_result)
            if conflicts:
                s5_decision = await self._invoke_s5_for_conflict(
                    conflicts, task_id
                )
                for conflict in conflicts:
                    self.log.log_conflict(task_id,
                                         conflict.get("s3_position", ""),
                                         conflict.get("s4_position", ""))

            # Update viability metrics
            self._update_metrics(s1_results, audit_result)

            # Complete the task
            success = audit_result.get("audit_passed", True)
            current_task.status = "completed" if success else "failed"
            self.state.set_current_task(current_task)
            self.log.log_task_completed(task_id, success)

            return VSMCycleResult(
                task_id=task_id,
                success=success,
                summary=self._build_summary(s1_results, audit_result),
                agents_invoked=[r.agent for r in s1_results],
                audit_passed=audit_result.get("audit_passed"),
                conflicts=conflicts,
                adaptations=[a.to_dict() for a in adaptations],
                s1_results=s1_results
            )

        except Exception as e:
            # Log and handle error
            current_task.status = "failed"
            self.state.set_current_task(current_task)
            self.log.log_task_completed(task_id, success=False,
                                        summary=str(e))
            raise

    async def _invoke_s4(self, task: str, task_id: str) -> dict:
        """Invoke S4 (Intelligence) for strategic analysis."""
        self.log.log_agent_invoked("system4-strategy", task_id, task[:200])

        prompt = f"""Analyze this development task and provide strategic intelligence.

Task: {task}

Read the current viability metrics from .claude/vsm-state/viability-metrics.json if it exists.

Provide your analysis as JSON with:
- task_analysis (summary, scope, domains_involved)
- environment_context (relevant_files, dependencies, constraints)
- external_research (best_practices, patterns, documentation)
- risks (with severity and mitigation)
- opportunities
- strategic_recommendation (approach, priorities, complexity_assessment, specialist_recommendation)

Write your analysis to .claude/vsm-state/s4-environment.json"""

        result = await self._invoke_agent("system4-strategy", prompt)

        # Read the S4 environment file
        s4_env = self.state.get_s4_environment()
        if s4_env:
            return {
                "analysis": s4_env.analysis,
                "risks": s4_env.risks,
                "opportunities": s4_env.opportunities,
                "recommended_approach": s4_env.recommended_approach
            }
        return {"analysis": result.output}

    async def _invoke_s3(self, task: str, s4_analysis: dict,
                        task_id: str) -> dict:
        """Invoke S3 (Control) for resource allocation."""
        self.log.log_agent_invoked("system3-control", task_id)

        # Get complexity adjustment from adaptations
        complexity_adj = self.adaptation.get_complexity_adjustment()

        prompt = f"""Determine resource allocation for this task.

Task: {task}

S4 Strategic Analysis:
{json.dumps(s4_analysis, indent=2)}

Read the agent registry from .claude/vsm-state/agent-registry.json
Read viability metrics from .claude/vsm-state/viability-metrics.json

Complexity threshold adjustment: {complexity_adj} (negative means use specialists earlier)

Provide your allocation decision as JSON with:
- complexity (simple|medium|complex)
- complexity_confidence
- complexity_rationale
- selected_agents (list with agent, role, order, task_focus)
- execution_mode (sequential|parallel|mixed)
- execution_plan (steps with agents and actions)
- synergies
- risks
- escalation_triggers

Write your allocation to .claude/vsm-state/s3-allocations.json"""

        result = await self._invoke_agent("system3-control", prompt)

        # Read the S3 allocation file
        allocation = self.state.get_s3_allocation()
        if allocation:
            return {
                "complexity": allocation.complexity,
                "selected_agents": allocation.selected_agents,
                "rationale": allocation.rationale
            }
        return {"allocation": result.output}

    async def _invoke_s2(self, s3_allocation: dict, task_id: str) -> dict:
        """Invoke S2 (Coordination) for execution scheduling."""
        self.log.log_agent_invoked("system2-coordination", task_id)

        increase_s2 = self.adaptation.should_increase_s2()

        prompt = f"""Create an execution schedule for the allocated agents.

S3 Allocation:
{json.dumps(s3_allocation, indent=2)}

{"IMPORTANT: Increased coordination is required due to recent oscillation issues." if increase_s2 else ""}

Provide your coordination plan as JSON with:
- execution_schedule (phases with agents, actions, files_locked, completion_signal)
- parallel_groups (if applicable)
- conflict_zones (resources with potential conflicts)
- handoff_protocols (from agent to agent)
- monitoring_points

Focus on preventing conflicts and oscillation between agents."""

        result = await self._invoke_agent("system2-coordination", prompt)
        return {"plan": result.output}

    async def _execute_s1_agents(self, s2_plan: dict, s3_allocation: dict,
                                 task_id: str) -> List[AgentResult]:
        """Execute S1 (Operations) agents according to the plan."""
        results = []

        # Parse selected agents from allocation
        agents = s3_allocation.get("selected_agents", [])
        if isinstance(agents, str):
            # Parse if it's a string
            try:
                agents = json.loads(agents)
            except:
                agents = [{"agent": "generalist-coder", "role": "primary"}]

        # Check if we should parallelize
        should_parallel = self.adaptation.should_parallelize()

        for agent_info in agents:
            agent_name = agent_info.get("agent", agent_info) if isinstance(agent_info, dict) else agent_info

            # Check if review step should be added
            if self.adaptation.should_add_review_step(agent_name):
                review_result = await self._invoke_s1_agent(
                    "s1-reviewer", task_id,
                    f"Review before {agent_name} executes"
                )
                results.append(review_result)

            # Invoke the agent
            task_focus = agent_info.get("task_focus", "") if isinstance(agent_info, dict) else ""
            result = await self._invoke_s1_agent(
                f"s1-{agent_name}", task_id, task_focus
            )
            results.append(result)

            # Update agent status
            self.state.update_agent_status(
                agent_name,
                "available",
                None
            )

        return results

    async def _invoke_s1_agent(self, agent_name: str, task_id: str,
                              focus: str = "") -> AgentResult:
        """Invoke a single S1 agent."""
        self.log.log_agent_invoked(agent_name, task_id)

        current_task = self.state.get_current_task()
        task_desc = current_task.description if current_task else ""

        prompt = f"""Execute your assigned task.

Task: {task_desc}
Focus: {focus}

Read the current task from .claude/vsm-state/current-task.json
Read your coordination plan from .claude/vsm-state/coordination-plan.json if it exists

Complete your work and report results as JSON with:
- status (completed|partial|blocked)
- changes_made
- files_modified
- verification
- blockers (if any)
- handoff_notes"""

        result = await self._invoke_agent(agent_name, prompt)

        self.log.log_agent_completed(agent_name, task_id, result.success)

        return result

    async def _invoke_s3_star(self, task: str, s1_results: List[AgentResult],
                             task_id: str) -> dict:
        """Invoke S3* (Audit) to verify results."""
        self.log.log_agent_invoked("system3-audit", task_id)

        # Summarize S1 results
        results_summary = "\n".join([
            f"- {r.agent}: {'Success' if r.success else 'Failed'}"
            for r in s1_results
        ])

        prompt = f"""Audit the work completed by S1 agents.

Task: {task}

S1 Results:
{results_summary}

Perform a quality audit and report as JSON with:
- audit_passed (true|false)
- overall_score
- verification (files_verified, changes_confirmed, discrepancies)
- quality_assessment (code_quality, conventions_followed, issues_found)
- completeness (requirements_met, missing_items)
- oscillation_check (oscillation_detected, evidence)
- recommendations
- metrics_update"""

        result = await self._invoke_agent("system3-audit", prompt)

        # Parse audit result
        try:
            audit_data = json.loads(result.output)
            self.log.log_audit(task_id,
                              audit_data.get("audit_passed", True),
                              audit_data.get("quality_assessment", {}).get("issues_found", []))
            return audit_data
        except:
            return {"audit_passed": result.success}

    async def _invoke_s5_for_approval(self, task: str, s4_analysis: dict,
                                      s3_allocation: dict, task_id: str) -> bool:
        """Invoke S5 for approval of S3 allocation."""
        self.log.log_agent_invoked("system5-policy", task_id)

        prompt = f"""Review and approve S3's resource allocation.

Task: {task}

S4 Analysis:
{json.dumps(s4_analysis, indent=2)}

S3 Allocation:
{json.dumps(s3_allocation, indent=2)}

This approval is required due to recent S3/S4 conflicts.

Decide whether to approve this allocation. Return JSON with:
- approved (true|false)
- rationale
- modifications (if any changes needed)"""

        result = await self._invoke_agent("system5-policy", prompt)

        try:
            decision = json.loads(result.output)
            approved = decision.get("approved", True)
            self.log.log_policy_decision(
                task_id,
                "approved" if approved else "rejected",
                decision.get("rationale", "")
            )
            return approved
        except:
            return True

    async def _invoke_s5_for_conflict(self, conflicts: List[dict],
                                       task_id: str) -> dict:
        """Invoke S5 to resolve S3/S4 conflicts."""
        self.log.log_agent_invoked("system5-policy", task_id)

        prompt = f"""Resolve conflicts between S3 (Control) and S4 (Intelligence).

Conflicts detected:
{json.dumps(conflicts, indent=2)}

Read context from:
- .claude/vsm-state/s3-allocations.json
- .claude/vsm-state/s4-environment.json
- .claude/vsm-state/viability-metrics.json

Provide resolution as JSON with:
- decision
- rationale
- policy_update (optional)
- s3_guidance
- s4_guidance
- priority_order"""

        result = await self._invoke_agent("system5-policy", prompt)

        try:
            decision = json.loads(result.output)
            self.log.log_policy_decision(
                task_id,
                decision.get("decision", "resolved"),
                decision.get("rationale", "")
            )
            return decision
        except:
            return {"decision": "resolved"}

    def _detect_conflicts(self, s3_result: dict, s4_result: dict) -> List[dict]:
        """Detect conflicts between S3 and S4 positions."""
        conflicts = []

        # Check complexity disagreement
        s3_complexity = s3_result.get("complexity", "medium")
        s4_recommendation = s4_result.get("recommended_approach", "")

        if isinstance(s4_recommendation, dict):
            s4_complexity = s4_recommendation.get("complexity_assessment", "medium")
        else:
            s4_complexity = "medium"

        if s3_complexity != s4_complexity:
            conflicts.append({
                "type": "complexity_disagreement",
                "s3_position": f"Assessed as {s3_complexity}",
                "s4_position": f"Recommended as {s4_complexity}"
            })
            self.state.record_s3_s4_conflict()

        return conflicts

    def _update_metrics(self, s1_results: List[AgentResult],
                       audit_result: dict) -> None:
        """Update viability metrics based on results."""
        # Record agent results
        for result in s1_results:
            agent_name = result.agent.replace("s1-", "")
            self.state.record_agent_result(agent_name, result.success)

        # Record audit result
        audit_passed = audit_result.get("audit_passed", True)
        self.state.record_audit_result(audit_passed)

        # Record task completion
        overall_success = all(r.success for r in s1_results) and audit_passed
        self.state.record_task_completion(overall_success)

        # Check for oscillation
        if audit_result.get("oscillation_check", {}).get("oscillation_detected"):
            self.state.record_oscillation()

    def _build_summary(self, s1_results: List[AgentResult],
                      audit_result: dict) -> str:
        """Build a summary of the VSM cycle."""
        agents = ", ".join([r.agent for r in s1_results])
        successes = sum(1 for r in s1_results if r.success)
        total = len(s1_results)
        audit_status = "passed" if audit_result.get("audit_passed") else "failed"

        return f"Completed with {successes}/{total} agents successful. Audit {audit_status}."

    def _generate_task_id(self) -> str:
        """Generate a unique task ID."""
        import hashlib
        timestamp = datetime.utcnow().isoformat()
        return hashlib.sha256(timestamp.encode()).hexdigest()[:8]

    async def _invoke_agent(self, agent_name: str, prompt: str) -> AgentResult:
        """
        Invoke a Claude Code agent.

        This uses the Claude Code CLI with the --agent flag to invoke
        a specific agent defined in the plugin.
        """
        try:
            # Build the command
            cmd = [
                self.claude_command,
                "--print",
                "--agent", agent_name,
                prompt
            ]

            # Run the command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.working_dir)
            )

            stdout, stderr = await process.communicate()

            success = process.returncode == 0
            output = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr and not success else None

            return AgentResult(
                agent=agent_name,
                success=success,
                output=output,
                error=error
            )

        except Exception as e:
            return AgentResult(
                agent=agent_name,
                success=False,
                output="",
                error=str(e)
            )
