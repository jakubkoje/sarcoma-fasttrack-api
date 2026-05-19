from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.api.v1.endpoints.utils import ensure_found
from app.db.database_connection import get_session
from app.models import Organization
from app.schemas.organization import OrganizationCreate, OrganizationRead
from app.services.fhir_generators import create_organization as create_organization_fhir
from app.services.fhir_client import upload_fhir_resource, get_fhir_resource
from app.services.fhir_extractors import extract_organization_data

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=List[OrganizationRead])
def list_organizations(
    session: Session = Depends(get_session),
) -> List[OrganizationRead]:
    """List organizations with data from database and FHIR server."""
    orgs = session.exec(select(Organization)).all()
    result = []

    for org in orgs:
        fhir_data = {}
        if org.fhir_id:
            fhir_resource = get_fhir_resource("Organization", org.fhir_id)
            if fhir_resource:
                fhir_data = extract_organization_data(fhir_resource)

        org_dict = org.model_dump(exclude_none=True)
        org_dict.update(fhir_data)
        result.append(OrganizationRead.model_validate(org_dict))

    return result


@router.post("", response_model=OrganizationRead, status_code=201)
def create_organization(
    payload: OrganizationCreate, session: Session = Depends(get_session)
) -> OrganizationRead:
    """
    Create organization and upload to FHIR server.

    This endpoint:
    1. Generates a unique FHIR ID
    2. Creates a FHIR Organization resource with organization data
    3. Uploads the resource to the FHIR server
    4. Stores the FHIR ID in the SQL database
    """
    # Generate a unique FHIR ID
    fhir_id = f"org-{uuid.uuid4()}"

    # Create FHIR Organization resource
    uploaded_fhir_id = None
    try:
        fhir_org = create_organization_fhir(
            id=fhir_id,
            name=payload.name,
            type_code=payload.type_code,
            address=payload.address,
            contact=payload.contact,
        )
        uploaded_fhir_id = upload_fhir_resource(fhir_org)
    except Exception:
        uploaded_fhir_id = None

    # Map simple address/contact into model fields
    org_data = payload.model_dump(exclude_none=True)
    if payload.address and "address_line" not in org_data:
        org_data["address_line"] = payload.address
    if payload.contact and "phone" not in org_data:
        org_data["phone"] = payload.contact

    # Create SQL record with FHIR ID (even if FHIR upload failed)
    org = Organization(fhir_id=uploaded_fhir_id, **org_data)
    session.add(org)
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
    session.refresh(org)
    return OrganizationRead.model_validate(org)


@router.get("/{org_id}", response_model=OrganizationRead)
def get_organization(
    org_id: int, session: Session = Depends(get_session)
) -> OrganizationRead:
    """Get organization detail with data from database and FHIR server."""
    org = session.get(Organization, org_id)
    ensure_found(bool(org), "Organization")

    fhir_data = {}
    if org.fhir_id:
        fhir_resource = get_fhir_resource("Organization", org.fhir_id)
        if fhir_resource:
            fhir_data = extract_organization_data(fhir_resource)

    org_dict = org.model_dump(exclude_none=True)
    org_dict.update(fhir_data)
    return OrganizationRead.model_validate(org_dict)


@router.get("/{org_id}/name")
def get_organization_name(org_id: int, session: Session = Depends(get_session)) -> dict:
    """
    Get organization name by organization ID.
    Tries database first, then falls back to FHIR if not found.
    """
    org = session.get(Organization, org_id)
    ensure_found(bool(org), "Organization")

    # Try to get name from database
    if org.name:
        return {"organization_id": org_id, "name": org.name}

    # Fall back to FHIR if not in database
    if org.fhir_id:
        fhir_resource = get_fhir_resource("Organization", org.fhir_id)
        if fhir_resource:
            fhir_data = extract_organization_data(fhir_resource)
            if fhir_data.get("name"):
                return {"organization_id": org_id, "name": fhir_data["name"]}

    # No name found
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Organization name not found in database or FHIR server",
    )
