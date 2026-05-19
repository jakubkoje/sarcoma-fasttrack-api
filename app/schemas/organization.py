from typing import Optional

from pydantic import BaseModel

from app.schemas.shared import BaseRead


class OrganizationCreate(BaseModel):
    # API-required fields
    name: str
    type_code: str
    address: str
    contact: str
    # Optional fields (DB/FHIR)
    fhir_id: Optional[str] = None
    ico: Optional[str] = None
    dic: Optional[str] = None
    email: Optional[str] = None
    address_city: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = None


class OrganizationRead(BaseRead):
    fhir_id: Optional[str] = None
    name: Optional[str] = None
    type_code: Optional[str] = None
    address: Optional[str] = None
    contact: Optional[str] = None
    ico: Optional[str] = None
    dic: Optional[str] = None
    email: Optional[str] = None
    address_city: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = None
