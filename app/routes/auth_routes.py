# app/routes/auth_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.role import Role

from app.schemas.auth_schemas import (
    RegisterRequest,
    LoginRequest,
    LoginResponse,
    UserResponse,
    ChangePasswordRequest,
)

from app.utils.password_utils import hash_password, verify_password
from app.utils.jwt_utils import create_access_token
from app.dependencies import get_current_user


router = APIRouter(tags=["Auth"])


# Note: Per requirements, user registration is handled by admins only via /admin/users
# Employees cannot self-register.


# -------------------------
# 2) Login (All roles)
# -------------------------
@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Load role name
    role = db.query(Role).filter(Role.id == user.role_id).first()
    role_name = role.name if role else "UNKNOWN"

    # Create token
    token = create_access_token(
        data={"user_id": user.id, "role": role_name}
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            role=role_name,
            is_active=user.is_active,
        ),
    )


# -------------------------
# 3) Get Current User
# -------------------------
@router.get("/auth/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    role_name = role.name if role else "UNKNOWN"

    return UserResponse(
        user_id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        phone=current_user.phone,
        role=role_name,
        is_active=current_user.is_active,
    )


# -------------------------
# 4) Change Password
# -------------------------
@router.post("/auth/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify old password
    if not verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect"
        )

    # Update new password
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()

    return {"message": "Password updated successfully"}
