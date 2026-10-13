"""Evidence-led API remediation recommendations; no configuration changes occur here."""

from sqlalchemy.orm import Session

from app.models.api import API, LifecycleState
from app.models.simulation import SimulationResult
from app.models.threat import ThreatFinding
from app.schemas.remediation import RemediationRecommendation
from app.services import simulation, threat_intelligence


UNKNOWN_CONTROLS_LIMITATION = (
    "Authentication, TLS, rate-limiting, and PII controls are unknown unless separately recorded; "
    "the recommendations do not claim that those controls are missing."
)


def _recommendation(
    key: str,
    priority: str,
    title: str,
    action: str,
    rationale: str,
    evidence: list[str],
    validation: str,
    reference_url: str | None = None,
) -> RemediationRecommendation:
    return RemediationRecommendation(
        key=key,
        priority=priority,  # type: ignore[arg-type]
        title=title,
        action=action,
        rationale=rationale,
        evidence=evidence,
        validation=validation,
        reference_url=reference_url,
    )


def _threat_recommendations(findings: list[ThreatFinding]) -> list[RemediationRecommendation]:
    recommendations = []
    for finding in findings:
        recommendations.append(_recommendation(
            key=f"threat-{finding.id}",
            priority="IMMEDIATE" if finding.severity == "CRITICAL" else "HIGH",
            title=f"Remediate {finding.advisory_id} in {finding.component_name}",
            action=(
                f"Review the advisory, then upgrade or patch {finding.component_name} {finding.component_version} "
                "to a vendor-approved version that is not listed as affected."
            ),
            rationale="A source-attributed advisory exactly matched a component and version recorded for this API.",
            evidence=[
                f"{finding.advisory_id} severity: {finding.severity}",
                f"Matched component: {finding.component_name} {finding.component_version}",
                finding.summary,
            ],
            validation=(
                "Run the application regression tests after the change, update the recorded component version, "
                "and run threat correlation again."
            ),
            reference_url=finding.source_url,
        ))
    return recommendations


def _simulation_recommendations(results: list[SimulationResult]) -> list[RemediationRecommendation]:
    recommendations = []
    by_scenario = {result.scenario: result for result in results}
    authentication = by_scenario.get("AUTHENTICATION_EVIDENCE_REVIEW")
    if authentication and authentication.status == "INSUFFICIENT_EVIDENCE":
        recommendations.append(_recommendation(
            key="verify-authentication-evidence",
            priority="MEDIUM",
            title="Verify authentication evidence",
            action="Confirm whether this endpoint requires authentication and record the mechanism in the inventory evidence.",
            rationale="The controlled review could not determine authentication requirements from the current inventory.",
            evidence=[authentication.evidence_summary],
            validation="Re-run the controlled simulation after the evidence is recorded; it should no longer report insufficient evidence.",
        ))
    rate_limit = by_scenario.get("RATE_LIMIT_EVIDENCE_REVIEW")
    if rate_limit and rate_limit.status == "INSUFFICIENT_EVIDENCE":
        recommendations.append(_recommendation(
            key="verify-rate-limit-evidence",
            priority="MEDIUM",
            title="Verify rate-limiting evidence",
            action="Confirm the applicable rate-limit policy and record the evidence; configure a policy only if the owner confirms one is required.",
            rationale="The controlled review could not determine rate-limiting coverage from the current inventory.",
            evidence=[rate_limit.evidence_summary],
            validation="Re-run the controlled simulation after the evidence is recorded; it should no longer report insufficient evidence.",
        ))
    return recommendations


def build_recommendations(db: Session, api: API) -> list[RemediationRecommendation]:
    """Build deterministic recommendations from persisted inventory evidence only."""
    recommendations: list[RemediationRecommendation] = []
    threat_findings = threat_intelligence.list_findings(db, api.id)
    simulation_results = simulation.list_results(db, api.id)
    recommendations.extend(_threat_recommendations(threat_findings))

    sources = set(api.sources or [api.source])
    if api.lifecycle_state == LifecycleState.ZOMBIE:
        recommendations.append(_recommendation(
            key="investigate-zombie-exposure",
            priority="HIGH",
            title="Investigate and contain the zombie API exposure",
            action="Identify the API owner and active clients; then remove or restrict the gateway route only after confirming the endpoint is not supported.",
            rationale="The lifecycle classifier found runtime activity without supported-surface evidence.",
            evidence=[api.classification_reason or "Lifecycle state is ZOMBIE."],
            validation="Confirm the endpoint is absent from the supported route set and monitor runtime logs for unexpected client impact after the approved change.",
        ))
    if not api.is_registered:
        recommendations.append(_recommendation(
            key="register-api-owner",
            priority="HIGH" if api.lifecycle_state == LifecycleState.ZOMBIE else "MEDIUM",
            title="Register the API and assign an owner",
            action="Add the API to the approved inventory and assign a responsible owner, or begin an approved retirement process if no owner accepts it.",
            rationale="Registration status is not confirmed in the current inventory.",
            evidence=["is_registered: false"],
            validation="Update the inventory record and re-run risk assessment; the registration finding should be removed.",
        ))
    if not api.is_documented:
        recommendations.append(_recommendation(
            key="document-api-contract",
            priority="HIGH" if "runtime_log" in sources else "MEDIUM",
            title="Reconcile and document the API contract",
            action="Confirm the endpoint with its owner and publish or update its OpenAPI contract; retire the route through change control if it is not supported.",
            rationale="Documentation status is not confirmed in the current inventory.",
            evidence=["is_documented: false"],
            validation="Run OpenAPI discovery after publishing the contract and verify that the endpoint has documentation evidence.",
        ))
    if "runtime_log" in sources and not ({"openapi", "git"} & sources):
        recommendations.append(_recommendation(
            key="reconcile-runtime-only-route",
            priority="HIGH",
            title="Reconcile the runtime-only route",
            action="Trace the observed route to source code and an owner; add supported-surface evidence or remove the route through the normal deployment process.",
            rationale="This endpoint is observed only in runtime logs, with no OpenAPI or Git evidence.",
            evidence=[f"Observed sources: {', '.join(sorted(sources))}"],
            validation="Repeat discovery from source and runtime logs; confirm the route is either documented or no longer observed.",
        ))
    if api.is_deprecated:
        recommendations.append(_recommendation(
            key="retire-deprecated-api",
            priority="MEDIUM",
            title="Complete the deprecation and retirement plan",
            action="Notify consumers of the replacement, define a sunset date, and remove the public route only after migration and owner approval.",
            rationale="The API is explicitly marked deprecated.",
            evidence=["is_deprecated: true"],
            validation="Verify client migration and then re-run lifecycle classification to record the final supported-surface state.",
        ))
    if api.is_removed_from_supported_surface:
        recommendations.append(_recommendation(
            key="verify-removed-surface",
            priority="HIGH",
            title="Verify removal from the supported surface",
            action="Confirm that gateway, routing, and deployment configuration no longer expose this route; preserve evidence of approval before removal.",
            rationale="The API is marked as removed from the supported surface.",
            evidence=["is_removed_from_supported_surface: true"],
            validation="After the approved change, verify there is no supported route and review runtime observations for residual traffic.",
        ))
    recommendations.extend(_simulation_recommendations(simulation_results))

    if not recommendations:
        recommendations.append(_recommendation(
            key="continue-monitoring",
            priority="LOW",
            title="Continue evidence-based monitoring",
            action="Keep inventory, lifecycle classification, and risk assessment current as new source or runtime evidence arrives.",
            rationale="No stored evidence currently requires a targeted remediation action.",
            evidence=[f"Lifecycle state: {api.lifecycle_state.value}", f"Risk score: {api.risk_score if api.risk_score is not None else 'not assessed'}"],
            validation="Review this recommendation after new discovery, threat, simulation, or risk evidence is persisted.",
        ))
    return recommendations


def limitations() -> list[str]:
    return [
        UNKNOWN_CONTROLS_LIMITATION,
        "Recommendations are advisory only. ZombieShield does not change routes, gateway policies, dependencies, or production configuration.",
    ]
