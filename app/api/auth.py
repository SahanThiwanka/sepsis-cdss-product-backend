from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.db.models import User
from app.schemas.auth import TokenOut, UserCreate, UserLogin, UserOut
from app.services.audit_service import create_audit_log

router = APIRouter()
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    username = payload.get("sub")

    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload.")

    user = db.query(User).filter(User.username == username).first()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive.")

    return user


def require_role(*allowed_roles: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to perform this action.",
            )

        return current_user

    return role_checker


@router.post("/bootstrap-admin", response_model=UserOut)
def bootstrap_admin(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user_count = db.query(User).count()

    if existing_user_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Bootstrap is disabled because users already exist.",
        )

    admin_user = User(
        username=user_data.username,
        full_name=user_data.full_name,
        role="admin",
        password_hash=hash_password(user_data.password),
        is_active=True,
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    create_audit_log(
        db=db,
        action="admin_bootstrapped",
        entity_type="user",
        entity_id=admin_user.id,
        actor=admin_user.username,
        details={
            "username": admin_user.username,
            "role": admin_user.role,
            "message": "Initial administrator account was created."
        }
    )

    return admin_user


@router.post("/login", response_model=TokenOut)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()

    if not user:
        create_audit_log(
            db=db,
            action="login_failed",
            entity_type="auth",
            actor=login_data.username,
            details={
                "username": login_data.username,
                "reason": "username_not_found"
            }
        )

        raise HTTPException(status_code=401, detail="Invalid username or password.")

    if not verify_password(login_data.password, user.password_hash):
        create_audit_log(
            db=db,
            action="login_failed",
            entity_type="auth",
            entity_id=user.id,
            actor=user.username,
            details={
                "username": user.username,
                "reason": "invalid_password"
            }
        )

        raise HTTPException(status_code=401, detail="Invalid username or password.")

    if not user.is_active:
        create_audit_log(
            db=db,
            action="login_failed",
            entity_type="auth",
            entity_id=user.id,
            actor=user.username,
            details={
                "username": user.username,
                "reason": "inactive_account"
            }
        )

        raise HTTPException(status_code=403, detail="User account is inactive.")

    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role,
        }
    )

    create_audit_log(
        db=db,
        action="login_success",
        entity_type="auth",
        entity_id=user.id,
        actor=user.username,
        details={
            "username": user.username,
            "role": user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/users", response_model=UserOut)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    existing_user = (
        db.query(User)
        .filter(User.username == user_data.username)
        .first()
    )

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists.")

    if user_data.role not in ["admin", "clinician", "researcher"]:
        raise HTTPException(status_code=400, detail="Invalid role.")

    new_user = User(
        username=user_data.username,
        full_name=user_data.full_name,
        role=user_data.role,
        password_hash=hash_password(user_data.password),
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    create_audit_log(
        db=db,
        action="user_created",
        entity_type="user",
        entity_id=new_user.id,
        actor=current_user.username,
        details={
            "created_username": new_user.username,
            "created_role": new_user.role,
            "created_by": current_user.username
        }
    )

    return new_user


@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    return db.query(User).order_by(User.created_at.desc()).all()