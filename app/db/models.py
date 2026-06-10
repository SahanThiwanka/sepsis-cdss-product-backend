from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="clinician", nullable=False)

    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_code = Column(String, unique=True, index=True, nullable=False)

    age = Column(Float, nullable=True)
    gender = Column(Float, nullable=True)
    unit1 = Column(Float, nullable=True)
    unit2 = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    observations = relationship("Observation", back_populates="patient")
    predictions = relationship("Prediction", back_populates="patient")
    alerts = relationship("Alert", back_populates="patient")


class Observation(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    iculos = Column(Float, nullable=True)

    observation_data = Column(JSON, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="observations")
    predictions = relationship("Prediction", back_populates="observation")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    observation_id = Column(Integer, ForeignKey("observations.id"), nullable=True)

    model_name = Column(String, nullable=False)
    model_version = Column(String, nullable=False)

    raw_probability = Column(Float, nullable=False)
    calibrated_probability = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)

    risk_level = Column(String, nullable=False)
    ai_alert = Column(Boolean, nullable=False)

    sirs_score = Column(Integer, nullable=True)
    sirs_positive = Column(Boolean, nullable=True)

    final_alert = Column(Boolean, nullable=False)
    priority = Column(String, nullable=False)
    recommendation = Column(Text, nullable=False)

    missing_features = Column(JSON, nullable=True)
    top_risk_factors = Column(JSON, nullable=True)
    top_protective_factors = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="predictions")
    observation = relationship("Observation", back_populates="predictions")
    alert = relationship("Alert", back_populates="prediction", uselist=False)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False)

    priority = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="alerts")
    prediction = relationship("Prediction", back_populates="alert")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=True)

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)

    actor = Column(String, default="system")
    details = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)