from datetime import date
from typing import Optional

from pydantic import BaseModel

from app.schemas.shared import BaseRead


class PatientBase(BaseModel):
    fhir_id: Optional[str] = None
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
    managing_organization_id: Optional[int] = None


class PatientCreate(PatientBase):
    # API-required fields
    first_name: str
    last_name: str
    address: str
    birth_number: str  # RČ
    phone: str
    email: Optional[str] = None
    managing_org_id: Optional[int] = None  # maps to managing_organization_id


class PatientRead(BaseRead, PatientBase):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address: Optional[str] = None
    birth_number: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    managing_org_id: Optional[int] = None
