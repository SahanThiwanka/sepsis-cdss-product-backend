from functools import lru_cache
from typing import Any

import numpy as np
import shap

from app.ml.model_loader import load_lightgbm_model


@lru_cache
def get_shap_explainer():
    model = load_lightgbm_model()
    return shap.TreeExplainer(model)


def extract_positive_class_shap_values(shap_values: Any) -> np.ndarray:
    """
    Handles different SHAP output formats for binary LightGBM models.
    Returns SHAP values for the positive/sepsis class.
    """

    if isinstance(shap_values, list):
        return np.asarray(shap_values[1][0])

    shap_array = np.asarray(shap_values)

    if shap_array.ndim == 3:
        return shap_array[0, :, 1]

    if shap_array.ndim == 2:
        return shap_array[0]

    raise ValueError(f"Unexpected SHAP values shape: {shap_array.shape}")


def explain_prediction(feature_df, missing_features: list[str], top_n: int = 5):
    """
    Returns clinician-friendly SHAP explanation.

    For the main UI, we hide:
    - missing indicator columns such as HR_missing
    - imputed/default original features that were not entered by the user
    """

    explainer = get_shap_explainer()

    shap_values = explainer.shap_values(feature_df)
    values = extract_positive_class_shap_values(shap_values)

    feature_names = list(feature_df.columns)
    feature_values = feature_df.iloc[0].to_dict()

    missing_set = set(missing_features)

    explanation_rows = []

    for feature, shap_value in zip(feature_names, values):
        # Hide missing-indicator columns from clinician-facing explanation
        if feature.endswith("_missing"):
            continue

        # Hide original features that were not provided and were filled by defaults
        if feature in missing_set:
            continue

        explanation_rows.append({
            "feature": feature,
            "feature_value": float(feature_values[feature]),
            "contribution": float(shap_value),
            "direction": "increases_risk" if shap_value > 0 else "decreases_risk"
        })

    top_risk_factors = sorted(
        [row for row in explanation_rows if row["contribution"] > 0],
        key=lambda x: x["contribution"],
        reverse=True
    )[:top_n]

    top_protective_factors = sorted(
        [row for row in explanation_rows if row["contribution"] < 0],
        key=lambda x: x["contribution"]
    )[:top_n]

    return {
        "top_risk_factors": top_risk_factors,
        "top_protective_factors": top_protective_factors
    }