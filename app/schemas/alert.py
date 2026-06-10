from datetime import datetime

from pydantic import BaseModel


class AlertOut(BaseModel):
    id: int
    patient_id: int
    patient_code: str
    prediction_id: int
    priority: str
    message: str
    is_active: bool
    created_at: datetime