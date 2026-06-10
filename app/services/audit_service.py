from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import AuditLog


def create_audit_log(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    actor: str = "system",
    details: Optional[dict] = None
):
    audit_log = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        patient_id=patient_id,
        actor=actor,
        details=details or {}
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log