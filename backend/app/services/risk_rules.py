"""Explainable, deterministic risk rules based on inventory evidence."""

from dataclasses import dataclass

from app.models.api import LifecycleState
from app.services.risk_features import RiskFeatureSet


@dataclass(frozen=True)
class RuleAssessment:
    score: float
    findings: list[str]


class DeterministicRiskRules:
    """Score confirmed inventory/lifecycle exposure signals, never unknown controls."""

    def assess(self, features: RiskFeatureSet, lifecycle_state: LifecycleState) -> RuleAssessment:
        values = features.values
        score = 0.0
        findings: list[str] = []

        if not values["registration_confirmed"]:
            score += 10
            findings.append("Registration status is not confirmed in the inventory.")
        if not values["documentation_confirmed"]:
            score += 10
            findings.append("Documentation status is not confirmed in the inventory.")
        if lifecycle_state == LifecycleState.ZOMBIE:
            score += 35
            findings.append("Lifecycle classification is ZOMBIE, indicating runtime exposure without supported-surface evidence.")
        if values["deprecated"]:
            score += 25
            findings.append("API is explicitly deprecated and should be reviewed for continued exposure.")
        if values["removed_from_supported_surface"]:
            score += 30
            findings.append("API has been removed from the supported surface.")
        if values["runtime_only_evidence"]:
            score += 15
            findings.append("API is observed only in runtime logs, without OpenAPI or Git evidence.")
        if values["source_count"] == 1:
            score += 5
            findings.append("Only one source of evidence is available for this API.")
        if values["endpoint_age_days"] >= 365:
            score += 5
            findings.append("Endpoint has been observed for at least one year; review its current control posture.")
        if values["known_threat_finding_count"]:
            threat_weight = min(30, 15 * int(values["known_threat_finding_count"]))
            score += threat_weight
            findings.append(f"{values['known_threat_finding_count']} source-attributed threat intelligence finding(s) match this API.")
        if values["simulation_finding_count"]:
            score += min(20, 10 * int(values["simulation_finding_count"]))
            findings.append(f"{values['simulation_finding_count']} controlled simulation scenario(s) observed elevated risk.")

        findings.append(
            "Authentication, TLS, rate limiting, and PII evidence are currently unknown; no missing control has been inferred."
        )
        return RuleAssessment(score=min(score, 100), findings=findings)
