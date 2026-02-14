# app/schemas/department_schemas.py

from pydantic import BaseModel, Field
from typing import Optional


class DepartmentCreateRequest(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)


class DepartmentResponse(BaseModel):
    department_id: int
    name: str
    description: Optional[str]
    
    class Config:
        from_attributes = True
