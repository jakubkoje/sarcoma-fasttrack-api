from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.api.v1.endpoints.utils import ensure_found
from app.db.database_connection import get_session
from app.models import Patient
from app.schemas.patient import PatientCreate, PatientRead
from app.services.fhir_generators import create_patient as create_patient_fhir
from app.services.fhir_client import upload_fhir_resource, get_fhir_resource
from app.services.fhir_extractors import extract_patient_data

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=List[PatientRead])
def list_patients(session: Session = Depends(get_session)) -> List[PatientRead]:
    """List patients with data from database and FHIR server."""
    patients = session.exec(select(Patient)).all()
    result = []

    for patient in patients:
        fhir_data = {}
        if patient.fhir_id:
            fhir_resource = get_fhir_resource("Patient", patient.fhir_id)
            if fhir_resource:
                fhir_data = extract_patient_data(fhir_resource)

        patient_dict = patient.model_dump(exclude_none=True)
        patient_dict.setdefault("fhir_id", patient.fhir_id or "")
        patient_dict.update(fhir_data)
        result.append(PatientRead.model_validate(patient_dict))

    return result


@router.post("", response_model=PatientRead, status_code=201)
def create_patient(
    payload: PatientCreate, session: Session = Depends(get_session)
) -> PatientRead:
    """
    Create patient and upload to FHIR server.

    This endpoint:
    1. Generates a unique FHIR ID
    2. Creates a FHIR Patient resource with demographic data
    3. Uploads the resource to the FHIR server
    4. Stores the FHIR ID in the SQL database
    """
    uploaded_fhir_id = None
    try:
        fhir_id = f"pat-{uuid.uuid4()}"
        fhir_patient = create_patient_fhir(
            id=fhir_id,
            first_name=payload.first_name or payload.given_name,
            last_name=payload.last_name or payload.family_name,
            address=payload.address or payload.address_text,
            birth_number=payload.birth_number or payload.identifier_rc,
            phone=payload.phone,
            email=payload.email,
            managing_org_id=payload.managing_org_id or payload.managing_organization_id,
        )
        uploaded_fhir_id = upload_fhir_resource(fhir_patient)
    except Exception:
        uploaded_fhir_id = None

    # Map legacy fields into model fields
    patient_data = payload.model_dump(exclude_none=True)
    if payload.first_name:
        patient_data.setdefault("given_name", payload.first_name)
    if payload.last_name:
        patient_data.setdefault("family_name", payload.last_name)
    if payload.address:
        patient_data.setdefault("address_text", payload.address)
    if payload.birth_number:
        patient_data.setdefault("identifier_rc", payload.birth_number)
    if payload.managing_org_id is not None:
        patient_data.setdefault("managing_organization_id", payload.managing_org_id)
    patient = Patient(fhir_id=uploaded_fhir_id, **patient_data)
    session.add(patient)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        constraint = getattr(getattr(exc, "orig", None), "diag", None)
        cname = getattr(constraint, "constraint_name", None)
        msg = (
            "fhir_id must be unique"
            if cname
            else f"Constraint violation ({getattr(exc, 'orig', exc)})"
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    session.refresh(patient)
    return PatientRead.model_validate(patient)


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(
    patient_id: int, session: Session = Depends(get_session)
) -> PatientRead:
    """Get patient detail with data from database and FHIR server."""
    patient = session.get(Patient, patient_id)
    ensure_found(bool(patient), "Patient")

    fhir_data = {}
    if patient.fhir_id:
        fhir_resource = get_fhir_resource("Patient", patient.fhir_id)
        if fhir_resource:
            fhir_data = extract_patient_data(fhir_resource)

    patient_dict = patient.model_dump(exclude_none=True)
    patient_dict.setdefault("fhir_id", patient.fhir_id or "")
    patient_dict.update(fhir_data)
    return PatientRead.model_validate(patient_dict)


@router.get("/{patient_id}/name")
def get_patient_name(patient_id: int, session: Session = Depends(get_session)) -> dict:
    """
    Get patient name by patient ID.
    Tries database first, then falls back to FHIR if not found.
    """
    patient = session.get(Patient, patient_id)
    ensure_found(bool(patient), "Patient")

    # Try to get name from database
    name_parts = []
    if patient.given_name:
        name_parts.append(patient.given_name)
    if patient.family_name:
        name_parts.append(patient.family_name)

    if name_parts:
        return {"patient_id": patient_id, "name": " ".join(name_parts)}

    # Fall back to FHIR if not in database
    if patient.fhir_id:
        fhir_resource = get_fhir_resource("Patient", patient.fhir_id)
        if fhir_resource:
            fhir_data = extract_patient_data(fhir_resource)
            fhir_name_parts = []
            if fhir_data.get("first_name"):
                fhir_name_parts.append(fhir_data["first_name"])
            if fhir_data.get("last_name"):
                fhir_name_parts.append(fhir_data["last_name"])
            if fhir_name_parts:
                return {"patient_id": patient_id, "name": " ".join(fhir_name_parts)}

    # No name found
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Patient name not found in database or FHIR server",
    )
