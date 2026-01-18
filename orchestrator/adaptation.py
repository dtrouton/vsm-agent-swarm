"""
Adaptation Engine for VSM Orchestrator

Implements automatic adaptation based on viability metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
import json

from .state_manager import StateManager, ViabilityMetrics


class AdaptationType(str, Enum):
    """Types of adaptations."""
    ADD_REVIEW_STEP = "add_review_step"
    LOWER_COMPLEXITY_THRESHOLD = "lower_complexity_threshold"
    INCREASE_S2_INVOLVEMENT = "increase_s2_involvement"
    REQUIRE_S5_APPROVAL = "require_s5_approval"
    PARALLELIZE_S1 = "parallelize_s1"
    TIGHTEN_S3_STAR = "tighten_s3_star"


@dataclass
class Adaptation:
    """An adaptation to apply to the system."""
    type: AdaptationType
    trigger: str
    effect: str
    applied_at: str = ""
    parameters: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "trigger": self.trigger,
            "effect": self.effect,
            "applied_at": self.applied_at,
            "parameters": self.parameters
        }


class AdaptationEngine:
    """
    Analyzes viability metrics and determines necessary adaptations.

    This implements the automatic adaptation system described in the VSM plan,
    where the system self-adjusts based on viability metrics.
    """

    # Thresholds for triggering adaptations
    AGENT_ERROR_THRESHOLD = 0.3
    ESCALATION_THRESHOLD = 0.5
    OSCILLATION_THRESHOLD = 0.2
    POLICY_CONFLICT_THRESHOLD = 3
    AUDIT_FAILURE_THRESHOLD = 0.2

    def __init__(self, state_manager: StateManager):
        self.state = state_manager

    def analyze_metrics(self, metrics: ViabilityMetrics) -> List[Adaptation]:
        """
        Analyze viability metrics and determine adaptations needed.

        Args:
            metrics: Current viability metrics

        Returns:
            List of adaptations to apply
        """
        adaptations = []

        # Check agent error rates
        for agent_name, error_rate in metrics.agent_errors.items():
            if error_rate > self.AGENT_ERROR_THRESHOLD:
                adaptations.append(Adaptation(
                    type=AdaptationType.ADD_REVIEW_STEP,
                    trigger=f"{agent_name}_errors",
                    effect=f"Add reviewer before {agent_name}",
                    parameters={"target_agent": agent_name}
                ))

        # Check completion rate (indicator of complexity threshold issues)
        if metrics.completion_rate < self.ESCALATION_THRESHOLD:
            adaptations.append(Adaptation(
                type=AdaptationType.LOWER_COMPLEXITY_THRESHOLD,
                trigger="low_completion_rate",
                effect="Use specialists earlier for lower complexity tasks"
            ))

        # Check oscillation rate
        if metrics.oscillation_rate > self.OSCILLATION_THRESHOLD:
            adaptations.append(Adaptation(
                type=AdaptationType.INCREASE_S2_INVOLVEMENT,
                trigger="high_oscillation",
                effect="More coordination between S1 agents"
            ))

        # Check S3/S4 conflicts
        if metrics.s3_s4_conflicts > self.POLICY_CONFLICT_THRESHOLD:
            adaptations.append(Adaptation(
                type=AdaptationType.REQUIRE_S5_APPROVAL,
                trigger="frequent_s3_s4_conflicts",
                effect="Require S5 approval for S3 allocation decisions"
            ))

        # Check audit pass rate
        if metrics.audit_pass_rate < (1 - self.AUDIT_FAILURE_THRESHOLD):
            adaptations.append(Adaptation(
                type=AdaptationType.TIGHTEN_S3_STAR,
                trigger="low_audit_pass_rate",
                effect="More frequent and thorough S3* audits"
            ))

        # Check if we can parallelize (high avg cycle iterations = slow execution)
        if metrics.avg_cycle_iterations > 1.5:
            adaptations.append(Adaptation(
                type=AdaptationType.PARALLELIZE_S1,
                trigger="slow_execution",
                effect="Run compatible S1 agents concurrently"
            ))

        return adaptations

    def apply_adaptations(self, adaptations: List[Adaptation]) -> None:
        """
        Apply adaptations and record them in metrics.

        Args:
            adaptations: List of adaptations to apply
        """
        if not adaptations:
            return

        metrics = self.state.get_viability_metrics()

        for adaptation in adaptations:
            # Check if this adaptation is already active
            active_types = [a.get("type") for a in metrics.active_adaptations]
            if adaptation.type.value in active_types:
                continue

            # Apply the adaptation
            adaptation.applied_at = datetime.utcnow().isoformat()

            # Record in metrics
            metrics.active_adaptations.append(adaptation.to_dict())

        self.state.update_viability_metrics(metrics)

    def get_active_adaptations(self) -> List[dict]:
        """Get currently active adaptations."""
        metrics = self.state.get_viability_metrics()
        return metrics.active_adaptations

    def clear_adaptation(self, adaptation_type: AdaptationType) -> None:
        """
        Clear an adaptation when it's no longer needed.

        Args:
            adaptation_type: Type of adaptation to clear
        """
        metrics = self.state.get_viability_metrics()
        metrics.active_adaptations = [
            a for a in metrics.active_adaptations
            if a.get("type") != adaptation_type.value
        ]
        self.state.update_viability_metrics(metrics)

    def should_add_review_step(self, before_agent: str) -> bool:
        """Check if a review step should be added before an agent."""
        for adaptation in self.get_active_adaptations():
            if (adaptation.get("type") == AdaptationType.ADD_REVIEW_STEP.value and
                adaptation.get("parameters", {}).get("target_agent") == before_agent):
                return True
        return False

    def should_require_s5_approval(self) -> bool:
        """Check if S5 approval is required for S3 decisions."""
        for adaptation in self.get_active_adaptations():
            if adaptation.get("type") == AdaptationType.REQUIRE_S5_APPROVAL.value:
                return True
        return False

    def should_increase_s2(self) -> bool:
        """Check if S2 involvement should be increased."""
        for adaptation in self.get_active_adaptations():
            if adaptation.get("type") == AdaptationType.INCREASE_S2_INVOLVEMENT.value:
                return True
        return False

    def should_parallelize(self) -> bool:
        """Check if S1 agents should be parallelized."""
        for adaptation in self.get_active_adaptations():
            if adaptation.get("type") == AdaptationType.PARALLELIZE_S1.value:
                return True
        return False

    def get_complexity_adjustment(self) -> float:
        """
        Get complexity threshold adjustment.

        Returns negative value to lower thresholds (use specialists earlier).
        """
        for adaptation in self.get_active_adaptations():
            if adaptation.get("type") == AdaptationType.LOWER_COMPLEXITY_THRESHOLD.value:
                return -0.15  # Lower threshold by 15%
        return 0.0
