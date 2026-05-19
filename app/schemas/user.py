from enum import Enum
from typing import Optional

from pydantic import BaseModel, model_validator

from app.schemas.shared import BaseRead


class UserRole(str, Enum):
    admin = "admin"
    doctor = "doctor"
    specialist = "specialist"
    coordinator = "coordinator"


class UserCreate(BaseModel):
    email: str
    password: str
    role: UserRole
    # Doctor-specific
    practitioner_name: Optional[str] = None  # Name for FHIR Practitioner resource
    organization_id: Optional[int] = None

    @model_validator(mode="after")
    def validate_role_fields(self) -> "UserCreate":
        # if self.role == UserRole.doctor:
        #     if not self.practitioner_name or self.organization_id is None:
        #         raise ValueError(
        #             "practitioner_name and organization_id are required for doctor role"
        #         )
        return self


class UserRead(BaseRead):
    email: str
    is_active: bool
    role: UserRole
    fhir_id: Optional[str] = None  # FHIR ID for doctors and practitioners
