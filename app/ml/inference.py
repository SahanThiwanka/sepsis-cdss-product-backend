from app.ml.explanation import explain_prediction
from app.ml.feature_builder import build_feature_dataframe
from app.ml.model_loader import (
    get_model_config,
    load_calibrator,
    load_lightgbm_model
)
from app.services.clinical_rules import calculate_sirs_score
from app.services.decision_support import build_decision_support


def assign_risk_level(calibrated_probability: float) -> str:
    if calibrated_probability >= 0.05:
        return "high"
    elif calibrated_probability >= 0.02:
        return "moderate"
    return "low"


def predict_sepsis_risk(patient_id, observation):
    model = load_lightgbm_model()
    calibrator = load_calibrator()
    config = get_model_config()

    feature_df, missing_features = build_feature_dataframe(observation)

    raw_probability = float(model.predict_proba(feature_df)[0, 1])
    calibrated_probability = float(
        calibrator.transform([raw_probability])[0]
    )

    threshold = float(config.get("threshold", 0.05))

    ai_alert = calibrated_probability >= threshold
    risk_level = assign_risk_level(calibrated_probability)

    clinical_rules = calculate_sirs_score(observation)

    decision_support = build_decision_support(
        calibrated_probability=calibrated_probability,
        ai_alert=ai_alert,
        risk_level=risk_level,
        clinical_rules=clinical_rules
    )

    explanation = explain_prediction(
        feature_df=feature_df,
        missing_features=missing_features,
        top_n=5
    )

    return {
        "patient_id": patient_id,
        "model_name": config.get("model_name"),
        "model_version": config.get("model_version"),
        "raw_probability": raw_probability,
        "calibrated_probability": calibrated_probability,
        "threshold": threshold,
        "risk_level": risk_level,
        "alert": ai_alert,
        "missing_features_count": len(missing_features),
        "missing_features": missing_features,
        "clinical_rules": clinical_rules,
        "decision_support": decision_support,
        "top_risk_factors": explanation["top_risk_factors"],
        "top_protective_factors": explanation["top_protective_factors"]
    }