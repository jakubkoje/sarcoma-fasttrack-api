from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class ImagingModality(str, Enum):
    US = "US"
    MRI = "MRI"
    CT = "CT"
    PET_CT = "PET_CT"
    PET_MRI = "PET_MRI"


class Organization(SQLModel, table=True):
    __tablename__ = "organizations"

    id: Optional[int] = Field(default=None, primary_key=True)
    fhir_id: Optional[str] = Field(default=None, unique=True)
    name: Optional[str] = None
    type_code: Optional[str] = None
    ico: Optional[str] = None
    dic: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_line: Optional[str] = None
    address_city: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = None


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(nullable=False, unique=True, index=True)
    role: str = Field(nullable=False, default="coordinator")
    salt: str = Field(nullable=False)
    hashed_password: str = Field(nullable=False)
    is_active: bool = Field(default=True, nullable=False)


class Doctor(SQLModel, table=True):
    __tablename__ = "doctors"

    id: Optional[int] = Field(default=None, primary_key=True)
    fhir_id: Optional[str] = Field(default=None, unique=True, nullable=True)
    user_id: int = Field(nullable=False, unique=True, foreign_key="users.id")
    organization_id: Optional[int] = Field(default=None, foreign_key="organizations.id")
    family_name: Optional[str] = None
    given_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    specialty_code: Optional[str] = None
    role_code: Optional[str] = None


class Patient(SQLModel, table=True):
    __tablename__ = "patients"

    id: Optional[int] = Field(default=None, primary_key=True)
    fhir_id: Optional[str] = Field(default=None, unique=True)
    identifier_rc: Optional[str] = None
    insurance_company_code: Optional[str] = None
    family_name: Optional[str] = None
    given_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_text: Optional[str] = None
    address_city: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    managing_organization_id: Optional[int] = Field(default=None, foreign_key="organizations.id")


class Report(SQLModel, table=True):
    __tablename__ = "reports"

    id: Optional[int] = Field(default=None, primary_key=True)
    fhir_id: Optional[str] = Field(default=None, unique=True)
    patient_id: Optional[int] = Field(default=None, foreign_key="patients.id")
    doctor_id: Optional[int] = Field(default=None, foreign_key="doctors.id")
    target_organization_id: Optional[int] = Field(default=None, foreign_key="organizations.id")
    status: str = Field(default="DRAFT", nullable=False)
    is_new_patient: Optional[bool] = None
    any_imaging_performed: Optional[bool] = None
    additional_imaging_planned: Optional[bool] = None
    additional_imaging_note: Optional[str] = None
    anamnesis: Optional[str] = None
    family_history: Optional[str] = None
    anticoagulant_medication: Optional[bool] = None
    anticoagulant_detail: Optional[str] = None
    histology_performed: Optional[bool] = None
    histology_date: Optional[date] = None
    histology_result: Optional[str] = None
    summary: Optional[str] = None
    mkn10_code: Optional[str] = None
    feedback_specialist: Optional[str] = None
    attachment_path: Optional[str] = None
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)


class ImagingExamination(SQLModel, table=True):
    __tablename__ = "imaging_examinations"

    id: Optional[int] = Field(default=None, primary_key=True)
    report_id: int = Field(nullable=False, foreign_key="reports.id")
    modality: Optional[ImagingModality] = Field(
        default=None,
        sa_type=SAEnum(ImagingModality, name="imaging_modality", native_enum=False),
    )
    exam_date: Optional[date] = None
    description: Optional[str] = None


class MKN10(SQLModel, table=True):
    __tablename__ = "mkn10_code"

    code: str = Field(nullable=False, primary_key=True)
    name: str = Field(nullable=False)
