from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import require_role
from app.core.database import get_db
from app.db.models import Alert, Patient, Prediction, User

router = APIRouter()


@router.get("/")
def get_model_monitoring(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "clinician", "researcher")),
):
    predictions = db.query(Prediction).all()

    total_predictions = len(predictions)

    if total_predictions == 0:
        return {
            "total_predictions": 0,
            "average_risk_score": 0,
            "high_risk_predictions": 0,
            "moderate_risk_predictions": 0,
            "low_risk_predictions": 0,
            "alert_rate": 0,
            "active_alerts": db.query(Alert).filter(Alert.is_active == True).count(),
            "risk_distribution": {
                "low": 0,
                "moderate": 0,
                "high": 0,
            },
            "daily_prediction_volume": [],
            "latest_predictions": [],
            "message": "No predictions available yet.",
        }

    high_risk_predictions = sum(
        1 for prediction in predictions if prediction.risk_level == "high"
    )
    moderate_risk_predictions = sum(
        1 for prediction in predictions if prediction.risk_level == "moderate"
    )
    low_risk_predictions = sum(
        1 for prediction in predictions if prediction.risk_level == "low"
    )

    average_risk_score = sum(
        prediction.calibrated_probability for prediction in predictions
    ) / total_predictions

    total_alerts = db.query(Alert).count()
    active_alerts = db.query(Alert).filter(Alert.is_active == True).count()

    alert_rate = total_alerts / total_predictions if total_predictions else 0

    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=13)

    daily_counts = defaultdict(int)

    for prediction in predictions:
        prediction_date = prediction.created_at.date()

        if start_date <= prediction_date <= today:
            daily_counts[prediction_date.isoformat()] += 1

    daily_prediction_volume = []

    for index in range(14):
        current_date = start_date + timedelta(days=index)

        daily_prediction_volume.append(
            {
                "date": current_date.isoformat(),
                "count": daily_counts[current_date.isoformat()],
            }
        )

    latest_prediction_rows = (
        db.query(Prediction, Patient.patient_code)
        .join(Patient, Prediction.patient_id == Patient.id)
        .order_by(Prediction.created_at.desc())
        .limit(10)
        .all()
    )

    latest_predictions = [
        {
            "patient_code": patient_code,
            "risk_level": prediction.risk_level,
            "calibrated_probability": prediction.calibrated_probability,
            "raw_probability": prediction.raw_probability,
            "created_at": prediction.created_at,
        }
        for prediction, patient_code in latest_prediction_rows
    ]

    return {
        "total_predictions": total_predictions,
        "average_risk_score": average_risk_score,
        "high_risk_predictions": high_risk_predictions,
        "moderate_risk_predictions": moderate_risk_predictions,
        "low_risk_predictions": low_risk_predictions,
        "alert_rate": alert_rate,
        "active_alerts": active_alerts,
        "risk_distribution": {
            "low": low_risk_predictions,
            "moderate": moderate_risk_predictions,
            "high": high_risk_predictions,
        },
        "daily_prediction_volume": daily_prediction_volume,
        "latest_predictions": latest_predictions,
        "message": "Model monitoring data loaded successfully.",
    }