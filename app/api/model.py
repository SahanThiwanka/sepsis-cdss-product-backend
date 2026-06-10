from fastapi import APIRouter, HTTPException

from app.ml.model_loader import (
    get_model_config,
    load_lightgbm_model,
    load_calibrator
)

router = APIRouter()


@router.get("/info")
def get_model_info():
    config = get_model_config()

    return {
        "model_name": config.get("model_name"),
        "base_config": config.get("base_config"),
        "model_version": config.get("model_version"),
        "calibration": config.get("calibration"),
        "threshold": config.get("threshold"),
        "normalized_cinc_utility": config.get("normalized_cinc_utility"),
        "brier_score": config.get("brier_score"),
        "risk_levels": config.get("risk_levels")
    }


@router.get("/load-test")
def model_load_test():
    try:
        model = load_lightgbm_model()
        calibrator = load_calibrator()
        config = get_model_config()

        feature_names = getattr(model, "feature_name_", None)
        n_features = getattr(model, "n_features_in_", None)
        best_iteration = getattr(model, "best_iteration_", None)

        return {
            "status": "success",
            "model_loaded": True,
            "calibrator_loaded": True,
            "model_type": type(model).__name__,
            "calibrator_type": type(calibrator).__name__,
            "model_name": config.get("model_name"),
            "model_version": config.get("model_version"),
            "threshold": config.get("threshold"),
            "n_features": n_features,
            "best_iteration": best_iteration,
            "feature_count_from_model": len(feature_names) if feature_names else None,
            "sample_features": feature_names[:10] if feature_names else []
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Model load test failed: {str(error)}"
        )