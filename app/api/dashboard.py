from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import require_role
from app.core.database import get_db
from app.db.models import Alert, Patient, Prediction, User

router = APIRouter()


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "clinician", "researcher")),
):
    total_patients = db.query(Patient).count()
    total_predictions = db.query(Prediction).count()
    active_alerts = db.query(Alert).filter(Alert.is_active == True).count()
    high_risk_predictions = (
        db.query(Prediction)
        .filter(Prediction.risk_level == "high")
        .count()
    )

    latest_alerts_query = (
        db.query(Alert, Patient.patient_code)
        .join(Patient, Alert.patient_id == Patient.id)
        .filter(Alert.is_active == True)
        .order_by(Alert.created_at.desc())
        .limit(5)
        .all()
    )

    latest_alerts = [
        {
            "id": alert.id,
            "patient_code": patient_code,
            "priority": alert.priority,
            "message": alert.message,
            "created_at": alert.created_at,
        }
        for alert, patient_code in latest_alerts_query
    ]

    return {
        "total_patients": total_patients,
        "total_predictions": total_predictions,
        "active_alerts": active_alerts,
        "high_risk_predictions": high_risk_predictions,
        "latest_alerts": latest_alerts,
    }