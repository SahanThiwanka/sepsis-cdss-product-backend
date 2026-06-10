from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.db.models import Alert, Observation, Patient, Prediction
from app.ml.inference import predict_sepsis_risk
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.audit_service import create_audit_log
from app.api.auth import require_role
from app.db.models import User

router = APIRouter()


def get_or_create_patient(db: Session, patient_code: str, observation: dict):
    patient = (
        db.query(Patient)
        .filter(Patient.patient_code == patient_code)
        .first()
    )

    if patient:
        return patient

    patient = Patient(
        patient_code=patient_code,
        age=observation.get("Age"),
        gender=observation.get("Gender"),
        unit1=observation.get("Unit1"),
        unit2=observation.get("Unit2")
    )

    db.add(patient)
    db.commit()
    db.refresh(patient)

    return patient


def save_prediction_to_database(
    db: Session,
    request: PredictionRequest,
    result: dict,
    actor: str = "system"
):
    if not request.patient_id:
        return None

    observation_data = request.observation

    patient = get_or_create_patient(
        db=db,
        patient_code=request.patient_id,
        observation=observation_data
    )

    observation = Observation(
        patient_id=patient.id,
        iculos=observation_data.get("ICULOS"),
        observation_data=observation_data
    )

    db.add(observation)
    db.commit()
    db.refresh(observation)

    clinical_rules = result["clinical_rules"]
    decision_support = result["decision_support"]

    prediction = Prediction(
        patient_id=patient.id,
        observation_id=observation.id,
        model_name=result["model_name"],
        model_version=result["model_version"],
        raw_probability=result["raw_probability"],
        calibrated_probability=result["calibrated_probability"],
        threshold=result["threshold"],
        risk_level=result["risk_level"],
        ai_alert=result["alert"],
        sirs_score=clinical_rules["sirs_score"],
        sirs_positive=clinical_rules["sirs_positive"],
        final_alert=decision_support["final_alert"],
        priority=decision_support["priority"],
        recommendation=decision_support["recommendation"],
        missing_features=result["missing_features"],
        top_risk_factors=result["top_risk_factors"],
        top_protective_factors=result["top_protective_factors"]
    )

    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    create_audit_log(
    db=db,
    action="prediction_created",
    entity_type="prediction",
    entity_id=prediction.id,
    patient_id=patient.id,
    actor=actor,
    details={
        "patient_code": patient.patient_code,
        "calibrated_probability": result["calibrated_probability"],
        "risk_level": result["risk_level"],
        "ai_alert": result["alert"],
        "final_alert": decision_support["final_alert"],
        "model_version": result["model_version"]
    }
)

    if decision_support["final_alert"]:
        existing_active_alert = (
            db.query(Alert)
            .filter(Alert.patient_id == patient.id)
            .filter(Alert.is_active == True)
            .first()
        )

        if not existing_active_alert:
            alert = Alert(
                patient_id=patient.id,
                prediction_id=prediction.id,
                priority=decision_support["priority"],
                message=decision_support["recommendation"],
                is_active=True
            )

            db.add(alert)
            db.commit()
            db.refresh(alert)

            create_audit_log(
                db=db,
                action="alert_created",
                entity_type="alert",
                entity_id=alert.id,
                patient_id=patient.id,
                actor=actor,
                details={
                    "patient_code": patient.patient_code,
                    "priority": alert.priority,
                    "message": alert.message
                }
            )

    return prediction


@router.post("/predict", response_model=PredictionResponse)
def predict(
    request: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "clinician")),
):
    try:
        result = predict_sepsis_risk(
            patient_id=request.patient_id,
            observation=request.observation
        )

        save_prediction_to_database(
            db=db,
            request=request,
            result=result,
            actor=current_user.username
        )

        return result

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(error)}"
        )


@router.get("/patient/{patient_code}")
def get_patient_predictions(
    patient_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "clinician", "researcher")),
):
    patient = (
        db.query(Patient)
        .filter(Patient.patient_code == patient_code)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found."
        )

    predictions = (
        db.query(Prediction)
        .filter(Prediction.patient_id == patient.id)
        .order_by(Prediction.created_at.desc())
        .all()
    )

    return [
        {
            "id": prediction.id,
            "patient_code": patient.patient_code,
            "model_name": prediction.model_name,
            "model_version": prediction.model_version,
            "raw_probability": prediction.raw_probability,
            "calibrated_probability": prediction.calibrated_probability,
            "threshold": prediction.threshold,
            "risk_level": prediction.risk_level,
            "ai_alert": prediction.ai_alert,
            "sirs_score": prediction.sirs_score,
            "sirs_positive": prediction.sirs_positive,
            "final_alert": prediction.final_alert,
            "priority": prediction.priority,
            "recommendation": prediction.recommendation,
            "top_risk_factors": prediction.top_risk_factors,
            "top_protective_factors": prediction.top_protective_factors,
            "created_at": prediction.created_at
        }
        for prediction in predictions
    ]

@router.get("/patient/{patient_code}/timeline")
def get_patient_timeline(
    patient_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "clinician", "researcher")),
):
    patient = (
        db.query(Patient)
        .filter(Patient.patient_code == patient_code)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found."
        )

    predictions = (
        db.query(Prediction, Observation)
        .outerjoin(Observation, Prediction.observation_id == Observation.id)
        .filter(Prediction.patient_id == patient.id)
        .order_by(Prediction.created_at.asc())
        .all()
    )

    timeline = []

    for prediction, observation in predictions:
        observation_data = observation.observation_data if observation else {}

        timeline.append({
            "prediction_id": prediction.id,
            "observation_id": observation.id if observation else None,
            "patient_code": patient.patient_code,
            "created_at": prediction.created_at,
            "iculos": observation.iculos if observation else None,
            "calibrated_probability": prediction.calibrated_probability,
            "raw_probability": prediction.raw_probability,
            "risk_level": prediction.risk_level,
            "ai_alert": prediction.ai_alert,
            "final_alert": prediction.final_alert,
            "priority": prediction.priority,
            "sirs_score": prediction.sirs_score,
            "sirs_positive": prediction.sirs_positive,
            "recommendation": prediction.recommendation,
            "observation": {
                "HR": observation_data.get("HR"),
                "O2Sat": observation_data.get("O2Sat"),
                "Temp": observation_data.get("Temp"),
                "SBP": observation_data.get("SBP"),
                "MAP": observation_data.get("MAP"),
                "DBP": observation_data.get("DBP"),
                "Resp": observation_data.get("Resp"),
                "Lactate": observation_data.get("Lactate"),
                "WBC": observation_data.get("WBC"),
                "Platelets": observation_data.get("Platelets"),
                "Creatinine": observation_data.get("Creatinine"),
                "ICULOS": observation_data.get("ICULOS"),
            }
        })

    return {
        "patient": {
            "id": patient.id,
            "patient_code": patient.patient_code,
            "age": patient.age,
            "gender": patient.gender,
            "unit1": patient.unit1,
            "unit2": patient.unit2,
            "created_at": patient.created_at,
        },
        "timeline": timeline
    }    