from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.api.auth import require_role
from app.core.database import engine, get_db
from app.db.models import User

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[2]
ARTIFACTS_DIR = BASE_DIR / "artifacts"

REQUIRED_ARTIFACTS = [
    "AB_LGBM_4_shallow_best.pkl",
    "ab_lightgbm_isotonic_calibrator.pkl",
    "feature_columns.json",
    "feature_defaults.json",
    "model_config.json",
]

REQUIRED_TABLES = [
    "users",
    "patients",
    "observations",
    "predictions",
    "alerts",
    "audit_logs",
    "alembic_version",
]


@router.get("/")
def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "clinician", "researcher")),
):
    checked_at = datetime.now(timezone.utc).isoformat()

    database_status = "healthy"
    database_message = "Database connection successful."

    try:
        db.execute(text("SELECT 1"))
    except Exception as error:
        database_status = "unhealthy"
        database_message = str(error)

    existing_tables = []
    missing_tables = []

    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        missing_tables = [
            table for table in REQUIRED_TABLES if table not in existing_tables
        ]
    except Exception as error:
        database_status = "unhealthy"
        database_message = f"Could not inspect database tables: {error}"

    artifact_checks = []

    for artifact_name in REQUIRED_ARTIFACTS:
        artifact_path = ARTIFACTS_DIR / artifact_name

        artifact_checks.append(
            {
                "name": artifact_name,
                "exists": artifact_path.exists(),
                "size_bytes": artifact_path.stat().st_size
                if artifact_path.exists()
                else 0,
            }
        )

    missing_artifacts = [
        item["name"] for item in artifact_checks if not item["exists"]
    ]

    model_status = "healthy" if not missing_artifacts else "unhealthy"

    overall_status = "healthy"

    if database_status != "healthy" or model_status != "healthy" or missing_tables:
        overall_status = "unhealthy"

    return {
        "overall_status": overall_status,
        "checked_at": checked_at,
        "backend": {
            "status": "healthy",
            "message": "FastAPI backend is running.",
        },
        "database": {
            "status": database_status,
            "message": database_message,
            "required_tables": REQUIRED_TABLES,
            "missing_tables": missing_tables,
        },
        "model_artifacts": {
            "status": model_status,
            "artifacts_directory": str(ARTIFACTS_DIR),
            "missing_artifacts": missing_artifacts,
            "files": artifact_checks,
        },
        "security": {
            "authenticated_user": current_user.username,
            "role": current_user.role,
        },
    }