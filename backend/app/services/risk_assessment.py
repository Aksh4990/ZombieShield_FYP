"""Risk orchestration combining explainable rules with synthetic ML output."""

from dataclasses import dataclass
from datetime import datetime, timezone

from app.models.api import API, LifecycleState, RiskLevel
from app.services.risk_features import RiskFeatureExtractor
from app.services.risk_ml import SyntheticMLRiskScorer
from app.services.risk_rules import DeterministicRiskRules


@dataclass(frozen=True)
class RiskAssessment:
    score: float
    level: RiskLevel
    features: dict
    findings: list[str]
    explanation: str
    assessed_at: datetime


class RiskAssessmentService:
    """Combine deterministic rules (60%) with synthetic ML tiering (40%)."""

    def __init__(self) -> None:
        self.extractor = RiskFeatureExtractor()
        self.rules = DeterministicRiskRules()
        self.ml_scorer = SyntheticMLRiskScorer()

    def assess(self, api: API, now: datetime | None = None) -> RiskAssessment:
        assessed_at = now or datetime.now(timezone.utc)
        features = self.extractor.extract(api, assessed_at)
        rule_result = self.rules.assess(features, api.lifecycle_state or LifecycleState.ACTIVE)
        ml_score = self.ml_scorer.score(features.values)
        score = round(min(100, (rule_result.score * 0.60) + (ml_score * 0.40)), 2)
        level = self._level_for(score)
        explanation = (
            f"Risk score {score:.2f}/100 ({level.value}) combines deterministic inventory rules "
            f"(60%, {rule_result.score:.2f}/100) and a synthetic-data ML score "
            f"(40%, {ml_score:.2f}/100)."
        )
        return RiskAssessment(score, level, features.values, rule_result.findings, explanation, assessed_at)

    @staticmethod
    def _level_for(score: float) -> RiskLevel:
        if score < 25:
            return RiskLevel.LOW
        if score < 50:
            return RiskLevel.MEDIUM
        if score < 75:
            return RiskLevel.HIGH
        return RiskLevel.CRITICAL


def persist_assessment(api: API, assessment: RiskAssessment) -> API:
    api.risk_score = assessment.score
    api.risk_level = assessment.level.value
    api.risk_features = assessment.features
    api.risk_findings = assessment.findings
    api.risk_explanation = assessment.explanation
    api.risk_assessed_at = assessment.assessed_at
    return api
