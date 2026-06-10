from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.db.models import Patient
from app.schemas.patient import PatientCreate, PatientOut
from app.api.auth import require_role
from app.db.models import User

router = APIRouter()


@router.post("/", response_model=PatientOut)
def create_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "clinician")),
):
    existing_patient = (
        db.query(Patient)
        .filter(Patient.patient_code == patient.patient_code)
        .first()
    )

    if existing_patient:
        raise HTTPException(
            status_code=400,
            detail="Patient already exists."
        )

    new_patient = Patient(
        patient_code=patient.patient_code,
        age=patient.age,
        gender=patient.gender,
        unit1=patient.unit1,
        unit2=patient.unit2
    )

    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)

    return new_patient


@router.get("/", response_model=list[PatientOut])
def get_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "clinician", "researcher")),
):
    return (
        db.query(Patient)
        .order_by(Patient.created_at.desc())
        .all()
    )