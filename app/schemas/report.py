from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from app.schemas.shared import BaseRead


class ReportStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUBMITTED = "SUBMITTED"
    SENT = "SENT"
    DONE = "DONE"
    ERROR = "ERROR"

    @property
    def cz(self) -> str:
        return {
            "DRAFT": "Koncept",
            "ACTIVE": "Aktivní",
            "SUBMITTED": "Odeslaný",
            "SENT": "Odesláno",
            "DONE": "Dokončeno",
            "ERROR": "Chyba",
        }.get(self.value, self.value)


class ReportBase(BaseModel):
    fhir_id: Optional[str] = None
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    target_organization_id: Optional[int] = None
    status: Optional[ReportStatus] = ReportStatus.DRAFT
    feedback_specialist: Optional[str] = None
    is_new_patient: Optional[bool] = None
    any_imaging_performed: Optional[bool] = None
    additional_imaging_planned: Optional[bool] = None
    additional_imaging_note: Optional[str] = None
    anamnesis: Optional[str] = None
    mkn10_code: Optional[str] = None
    family_history: Optional[str] = None
    anticoagulant_medication: Optional[bool] = None
    anticoagulant_detail: Optional[str] = None
    histology_performed: Optional[bool] = None
    histology_date: Optional[date] = None
    histology_result: Optional[str] = None
    summary: Optional[str] = None
    feedback_specialist: Optional[str] = None
    attachment_path: Optional[str] = None


class ReportCreate(ReportBase):
    patient_id: int
    doctor_id: int
    target_organization_id: int


class ReportStatusUpdate(BaseModel):
    """Schema for updating report status"""

    status: ReportStatus


class ReportRead(BaseRead, ReportBase):
    status: Optional[ReportStatus] = None
    status_cz: Optional[str] = None
    authored_on: Optional[str] = None  # FHIR authoredOn
    note: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    specialist: Optional[str] = None
    specialist_confidence: Optional[float] = None
    specialist: Optional[str] = None
    severity: Optional[str] = None
    severity_code: Optional[int] = None
    severity_confidence: Optional[float] = None
    overall_confidence: Optional[float] = None
