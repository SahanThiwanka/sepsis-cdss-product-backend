from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import require_role
from app.core.database import get_db
from app.db.models import AuditLog, User
from app.schemas.audit import AuditLogOut

router = APIRouter()


@router.get("/", response_model=list[AuditLogOut])
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    return (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(100)
        .all()
    )