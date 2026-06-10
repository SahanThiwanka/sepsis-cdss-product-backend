from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PatientCreate(BaseModel):
    patient_code: str
    age: Optional[float] = None
    gender: Optional[float] = None
    unit1: Optional[float] = None
    unit2: Optional[float] = None


class PatientOut(BaseModel):
    id: int
    patient_code: str
    age: Optional[float]
    gender: Optional[float]
    unit1: Optional[float]
    unit2: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True