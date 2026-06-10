from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: Optional[int]
    patient_id: Optional[int]
    actor: str
    details: dict
    created_at: datetime

    class Config:
        from_attributes = True