from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.db.models import Alert, Patient
from app.schemas.alert import AlertOut
from app.services.audit_service import create_audit_log
from app.api.auth import require_role
from app.db.models import User

router = APIRouter()


@router.get("/", response_model=list[AlertOut])
def get_alerts(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "clinician", "researcher")),
):
    query = (
        db.query(Alert, Patient.patient_code)
        .join(Patient, Alert.patient_id == Patient.id)
    )

    if active_only:
        query = query.filter(Alert.is_active == True)

    results = query.order_by(Alert.created_at.desc()).all()

    return [
        {
            "id": alert.id,
            "patient_id": alert.patient_id,
            "patient_code": patient_code,
            "prediction_id": alert.prediction_id,
            "priority": alert.priority,
            "message": alert.message,
            "is_active": alert.is_active,
            "created_at": alert.created_at,
        }
        for alert, patient_code in results
    ]


@router.patch("/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "clinician")),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found."
        )

    alert.is_active = False

    db.commit()
    db.refresh(alert)

    create_audit_log(
        db=db,
        action="alert_resolved",
        entity_type="alert",
        entity_id=alert.id,
        patient_id=alert.patient_id,
        actor=current_user.username,
        details={
            "message": "Alert marked as resolved."
        }
    )
    return {
        "message": "Alert resolved successfully.",
        "alert_id": alert.id,
        "is_active": alert.is_active
    }