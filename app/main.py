from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.alerts import router as alerts_router
from app.api.health import router as health_router
from app.api.model import router as model_router
from app.api.patients import router as patients_router
from app.api.predictions import router as predictions_router

from app.api.dashboard import router as dashboard_router
from app.api.audit_logs import router as audit_logs_router
from app.api.reports import router as reports_router
from app.api.auth import router as auth_router
from app.api import system_health
from app.api import monitoring

app = FastAPI(
    title="Sepsis CDSS API",
    description="Clinical decision support API for early sepsis risk prediction.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(model_router, prefix="/api/model", tags=["Model"])
app.include_router(predictions_router, prefix="/api/predictions", tags=["Predictions"])
app.include_router(patients_router, prefix="/api/patients", tags=["Patients"])
app.include_router(alerts_router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(audit_logs_router, prefix="/api/audit-logs", tags=["Audit Logs"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])
app.include_router(
    system_health.router,
    prefix="/api/system-health",
    tags=["System Health"],
)
app.include_router(
    monitoring.router,
    prefix="/api/monitoring",
    tags=["Monitoring"],
)

@app.get("/")
def root():
    return {
        "message": "Sepsis CDSS API is running",
        "docs": "/docs"
    }