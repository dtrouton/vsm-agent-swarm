"""
Complexity Analyzer for VSM Orchestrator

Assesses task complexity to help S3 determine appropriate agent allocation.
Uses heuristics based on task keywords, scope, and domain indicators.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Complexity(str, Enum):
    """Task complexity levels."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class AgentType(str, Enum):
    """Types of S1 agents."""
    GENERALIST = "generalist"
    FUNCTIONAL = "functional"
    DOMAIN = "domain"


@dataclass
class ComplexityAssessment:
    """Result of complexity analysis."""
    complexity: Complexity
    confidence: float  # 0.0 to 1.0
    rationale: str
    suggested_agents: list
    suggested_agent_types: list
    parallel_possible: bool = False
    keywords_found: list = field(default_factory=list)
    domain_signals: list = field(default_factory=list)
    scope_estimate: str = ""


# Keyword patterns for complexity detection
COMPLEXITY_KEYWORDS = {
    Complexity.SIMPLE: [
        r"\bfix\s+typo\b", r"\bupdate\s+comment\b", r"\brename\b",
        r"\bsimple\s+fix\b", r"\bquick\s+change\b", r"\bminor\b",
        r"\bsmall\s+change\b", r"\bone\s+line\b", r"\btrivial\b",
        r"\badd\s+log\b", r"\bformat\b", r"\blint\b"
    ],
    Complexity.MEDIUM: [
        r"\badd\s+feature\b", r"\bimplement\b", r"\bcreate\b",
        r"\bfix\s+bug\b", r"\bupdate\b", r"\bmodify\b",
        r"\bextend\b", r"\bintegrate\b", r"\btest\b"
    ],
    Complexity.COMPLEX: [
        r"\brefactor\b", r"\barchitect\b", r"\bredesign\b",
        r"\bmigrat\b", r"\boptimiz\b", r"\bscale\b",
        r"\bsecurity\b", r"\bperformance\b", r"\bdistributed\b",
        r"\bmicroservice\b", r"\bapi\s+design\b", r"\bbreaking\s+change\b"
    ]
}

# Domain detection patterns
DOMAIN_PATTERNS = {
    "frontend": [
        r"\breact\b", r"\bvue\b", r"\bangular\b", r"\bcss\b",
        r"\bui\b", r"\bux\b", r"\bcomponent\b", r"\bstyle\b",
        r"\bresponsive\b", r"\baccessibility\b", r"\ba11y\b",
        r"\bhtml\b", r"\bjavascript\b", r"\btypescript\b.*front"
    ],
    "backend": [
        r"\bapi\b", r"\bendpoint\b", r"\bserver\b", r"\bservice\b",
        r"\brest\b", r"\bgraphql\b", r"\bauth\b", r"\brouting\b",
        r"\bmiddleware\b", r"\bcontroller\b", r"\bbusiness\s+logic\b"
    ],
    "database": [
        r"\bsql\b", r"\bdatabase\b", r"\bdb\b", r"\bquery\b",
        r"\bmigration\b", r"\bschema\b", r"\btable\b", r"\bindex\b",
        r"\bpostgres\b", r"\bmysql\b", r"\bmongo\b", r"\bredis\b",
        r"\borm\b", r"\brelation\b"
    ],
    "infrastructure": [
        r"\bdocker\b", r"\bkubernetes\b", r"\bk8s\b", r"\bci\b",
        r"\bcd\b", r"\bpipeline\b", r"\bdeploy\b", r"\bterraform\b",
        r"\baws\b", r"\bgcp\b", r"\bazure\b", r"\binfra\b",
        r"\bcontainer\b", r"\bhelm\b", r"\bansible\b"
    ]
}

# Scope indicators
SCOPE_PATTERNS = {
    "single_file": [
        r"\bthis\s+file\b", r"\bin\s+[\w./]+\.\w+\b", r"\bsingle\s+file\b"
    ],
    "multi_file": [
        r"\bacross\b", r"\bmultiple\s+files\b", r"\bseveral\b",
        r"\ball\s+files\b", r"\bcodebase\b"
    ],
    "cross_module": [
        r"\bmodule\b", r"\bpackage\b", r"\bcross-cutting\b",
        r"\bsystem-wide\b", r"\bglobal\b"
    ]
}


class ComplexityAnalyzer:
    """Analyzes task complexity for agent allocation."""

    def __init__(self, viability_metrics: Optional[dict] = None):
        """
        Initialize analyzer.

        Args:
            viability_metrics: Current viability metrics for adaptive thresholds
        """
        self.metrics = viability_metrics or {}
        self.threshold_adjustment = self._calculate_threshold_adjustment()

    def _calculate_threshold_adjustment(self) -> float:
        """
        Calculate threshold adjustment based on viability metrics.

        If recent tasks have had high escalation rates, lower the thresholds
        to use specialists earlier.
        """
        # Default: no adjustment
        adjustment = 0.0

        # Check if we should be more conservative (use specialists earlier)
        if self.metrics:
            # High error rates suggest we need specialists sooner
            avg_error = sum(self.metrics.get("agent_errors", {}).values()) / max(
                len(self.metrics.get("agent_errors", {})), 1
            )
            if avg_error > 0.2:
                adjustment -= 0.15  # Lower thresholds

            # High oscillation suggests more coordination needed
            if self.metrics.get("oscillation_rate", 0) > 0.15:
                adjustment -= 0.1

        return adjustment

    def analyze(self, task_description: str,
                user_hint: Optional[str] = None) -> ComplexityAssessment:
        """
        Analyze task complexity.

        Args:
            task_description: The task to analyze
            user_hint: Optional explicit complexity hint from user

        Returns:
            ComplexityAssessment with complexity level and recommendations
        """
        task_lower = task_description.lower()

        # Check for explicit user hint first
        if user_hint:
            hint_lower = user_hint.lower()
            if "simple" in hint_lower:
                return self._create_assessment(
                    Complexity.SIMPLE, 0.95, "User specified simple",
                    task_lower, override=True
                )
            elif "complex" in hint_lower:
                return self._create_assessment(
                    Complexity.COMPLEX, 0.95, "User specified complex",
                    task_lower, override=True
                )
            elif "medium" in hint_lower:
                return self._create_assessment(
                    Complexity.MEDIUM, 0.95, "User specified medium",
                    task_lower, override=True
                )

        # Calculate scores for each complexity level
        scores = {
            Complexity.SIMPLE: self._calculate_keyword_score(
                task_lower, COMPLEXITY_KEYWORDS[Complexity.SIMPLE]
            ),
            Complexity.MEDIUM: self._calculate_keyword_score(
                task_lower, COMPLEXITY_KEYWORDS[Complexity.MEDIUM]
            ),
            Complexity.COMPLEX: self._calculate_keyword_score(
                task_lower, COMPLEXITY_KEYWORDS[Complexity.COMPLEX]
            )
        }

        # Apply threshold adjustment
        scores[Complexity.COMPLEX] += self.threshold_adjustment
        scores[Complexity.MEDIUM] += self.threshold_adjustment * 0.5

        # Detect domains
        domains = self._detect_domains(task_lower)

        # Adjust for multi-domain (increases complexity)
        if len(domains) > 1:
            scores[Complexity.COMPLEX] += 0.3

        # Detect scope
        scope = self._detect_scope(task_lower)
        if scope == "cross_module":
            scores[Complexity.COMPLEX] += 0.2
        elif scope == "multi_file":
            scores[Complexity.MEDIUM] += 0.15

        # Determine final complexity
        if scores[Complexity.COMPLEX] > 0.4:
            complexity = Complexity.COMPLEX
        elif scores[Complexity.SIMPLE] > 0.5 and scores[Complexity.COMPLEX] < 0.2:
            complexity = Complexity.SIMPLE
        else:
            complexity = Complexity.MEDIUM

        # Calculate confidence
        max_score = max(scores.values())
        second_score = sorted(scores.values())[-2]
        confidence = min(0.95, 0.5 + (max_score - second_score))

        # Build rationale
        rationale = self._build_rationale(scores, domains, scope)

        return self._create_assessment(
            complexity, confidence, rationale, task_lower,
            domains=domains, scope=scope
        )

    def _calculate_keyword_score(self, text: str, patterns: list) -> float:
        """Calculate score based on keyword matches."""
        score = 0.0
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.25
        return min(score, 1.0)

    def _detect_domains(self, text: str) -> list:
        """Detect which domains are relevant to the task."""
        domains = []
        for domain, patterns in DOMAIN_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    if domain not in domains:
                        domains.append(domain)
                    break
        return domains

    def _detect_scope(self, text: str) -> str:
        """Detect the scope of changes."""
        for scope, patterns in SCOPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return scope
        return "unknown"

    def _build_rationale(self, scores: dict, domains: list, scope: str) -> str:
        """Build explanation for the complexity assessment."""
        parts = []

        # Explain keyword signals
        max_complexity = max(scores.keys(), key=lambda k: scores[k])
        if scores[max_complexity] > 0.3:
            parts.append(f"Keywords suggest {max_complexity.value} complexity")

        # Explain domain signals
        if domains:
            if len(domains) > 1:
                parts.append(f"Spans multiple domains: {', '.join(domains)}")
            else:
                parts.append(f"Domain: {domains[0]}")

        # Explain scope
        if scope != "unknown":
            parts.append(f"Scope: {scope.replace('_', ' ')}")

        return "; ".join(parts) if parts else "No strong signals detected"

    def _create_assessment(self, complexity: Complexity, confidence: float,
                          rationale: str, task_text: str,
                          domains: Optional[list] = None,
                          scope: str = "unknown",
                          override: bool = False) -> ComplexityAssessment:
        """Create the final assessment with agent recommendations."""
        domains = domains or []

        # Determine suggested agents based on complexity and domains
        suggested_agents = []
        suggested_types = []

        if complexity == Complexity.SIMPLE:
            suggested_agents = ["generalist-coder"]
            suggested_types = [AgentType.GENERALIST]
            parallel = False

        elif complexity == Complexity.MEDIUM:
            # Use functional specialists
            suggested_agents = ["code-writer"]
            suggested_types = [AgentType.FUNCTIONAL]

            # Add tester if testing is mentioned
            if re.search(r"\btest\b", task_text):
                suggested_agents.append("tester")

            # Add reviewer for quality-sensitive tasks
            if re.search(r"\breview\b|\bquality\b", task_text):
                suggested_agents.append("reviewer")

            parallel = len(suggested_agents) == 1  # Only parallel if single agent

        else:  # COMPLEX
            # Use domain specialists
            if domains:
                suggested_agents = [d for d in domains]
                suggested_types = [AgentType.DOMAIN] * len(domains)
            else:
                # Default to functional specialists for unclassified complex tasks
                suggested_agents = ["code-writer", "reviewer"]
                suggested_types = [AgentType.FUNCTIONAL, AgentType.FUNCTIONAL]

            # Always add tester and reviewer for complex tasks
            if "tester" not in suggested_agents:
                suggested_agents.append("tester")
                suggested_types.append(AgentType.FUNCTIONAL)
            if "reviewer" not in suggested_agents:
                suggested_agents.append("reviewer")
                suggested_types.append(AgentType.FUNCTIONAL)

            # Complex tasks can often parallelize domain work
            parallel = len(domains) > 1

        # Find keywords that matched
        keywords_found = []
        for pattern in (COMPLEXITY_KEYWORDS[Complexity.SIMPLE] +
                       COMPLEXITY_KEYWORDS[Complexity.MEDIUM] +
                       COMPLEXITY_KEYWORDS[Complexity.COMPLEX]):
            match = re.search(pattern, task_text, re.IGNORECASE)
            if match:
                keywords_found.append(match.group())

        return ComplexityAssessment(
            complexity=complexity,
            confidence=confidence,
            rationale=rationale,
            suggested_agents=suggested_agents,
            suggested_agent_types=suggested_types,
            parallel_possible=parallel,
            keywords_found=keywords_found,
            domain_signals=domains,
            scope_estimate=scope
        )

    def get_agent_recommendation(self, assessment: ComplexityAssessment) -> dict:
        """
        Get detailed agent recommendation from assessment.

        Returns dict suitable for S3 allocation decision.
        """
        return {
            "complexity": assessment.complexity.value,
            "confidence": assessment.confidence,
            "primary_agents": assessment.suggested_agents[:2],
            "support_agents": assessment.suggested_agents[2:],
            "agent_types": [t.value for t in assessment.suggested_agent_types],
            "parallel_execution": assessment.parallel_possible,
            "rationale": assessment.rationale,
            "domains": assessment.domain_signals,
            "scope": assessment.scope_estimate
        }
