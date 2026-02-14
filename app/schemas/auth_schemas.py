# app/schemas/auth_schemas.py

from pydantic import BaseModel, EmailStr, Field


# ----------------------------
# Requests
# ----------------------------

class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=3, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    password: str = Field(min_length=6, max_length=50)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1)
    new_password: str = Field(min_length=6, max_length=50)


class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=6, max_length=50)


# ----------------------------
# Responses
# ----------------------------

class UserResponse(BaseModel):
    id: int  # Changed from user_id to match database column
    full_name: str
    email: str
    phone: str | None
    role: str
    is_active: bool


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
