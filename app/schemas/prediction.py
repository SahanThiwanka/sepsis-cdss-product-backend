from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    patient_id: Optional[str] = Field(default=None, examples=["P001"])
    observation: Dict[str, Optional[float]] = Field(
        ...,
        description="Dictionary of patient vitals/labs using model feature names."
    )


class ExplanationFactor(BaseModel):
    feature: str
    feature_value: float
    contribution: float
    direction: str


class ClinicalRules(BaseModel):
    sirs_score: int
    sirs_positive: bool
    criteria: Dict[str, bool]


class DecisionSupport(BaseModel):
    final_alert: bool
    priority: str
    recommendation: str
    rationale: List[str]


class PredictionResponse(BaseModel):
    patient_id: Optional[str]
    model_name: str
    model_version: str
    raw_probability: float
    calibrated_probability: float
    threshold: float
    risk_level: str
    alert: bool
    missing_features_count: int
    missing_features: List[str]
    clinical_rules: ClinicalRules
    decision_support: DecisionSupport
    top_risk_factors: List[ExplanationFactor] = Field(default_factory=list)
    top_protective_factors: List[ExplanationFactor] = Field(default_factory=list)