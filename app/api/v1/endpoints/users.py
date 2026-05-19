from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.api.deps import require_user
from app.core.security import generate_salt, hash_password
from app.db.database_connection import get_session
from app.models import User, Doctor, Organization
from app.schemas.user import UserCreate, UserRead, UserRole
from app.services.fhir_generators import (
    create_practitioner as create_practitioner_fhir,
    create_practitioner_role as create_practitioner_role_fhir,
)
from app.services.fhir_client import upload_fhir_resource, get_fhir_resource
from app.services.fhir_extractors import extract_practitioner_data

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserRead], dependencies=[Depends(require_user)])
def list_users(session: Session = Depends(get_session)) -> List[UserRead]:
    """List users with FHIR data for doctors."""
    users = session.exec(select(User)).all()
    result = []
    for user in users:
        result.append(UserRead.model_validate(user))
    return result


@router.post("", response_model=UserRead, status_code=201)
def create_user(
    payload: UserCreate, session: Session = Depends(get_session)
) -> UserRead:
    """
    Create user and create FHIR Practitioner resource for doctors/specialists.

    This endpoint:
    1. Creates a User account
    2. For doctors/specialists: Generates FHIR ID and creates FHIR Practitioner resource
    3. Uploads Practitioner resource to FHIR server
    4. Optionally creates PractitionerRole for doctors
    5. Stores the FHIR ID in the SQL database
    """
    # Validate organization for doctors if provided
    organization = None
    if payload.role == UserRole.doctor:
        organization = session.get(Organization, payload.organization_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not found"
            )

    salt = generate_salt()
    hashed_pw = hash_password(payload.password, salt)
    user = User(
        email=payload.email,
        hashed_password=hashed_pw,
        salt=salt,
        role=payload.role.value,
        is_active=True,
    )
    session.add(user)
    try:
        session.flush()  # get user.id without committing
    except IntegrityError as exc:
        session.rollback()
        constraint = getattr(getattr(exc, "orig", None), "diag", None)
        constraint_name = getattr(constraint, "constraint_name", None)
        msg = (
            "Email already registered"
            if constraint_name == "users_email_key"
            else f"Constraint violation ({constraint_name or exc.orig})"
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    # Create FHIR Practitioner resource for doctors/specialists
    uploaded_fhir_id = None
    if payload.role in [UserRole.doctor, UserRole.specialist]:
        try:
            fhir_id = f"prac-{uuid.uuid4()}"
            fhir_practitioner = create_practitioner_fhir(
                id=fhir_id, name=payload.practitioner_name
            )
            uploaded_fhir_id = upload_fhir_resource(fhir_practitioner)

            if payload.role == UserRole.doctor and organization:
                role_fhir_id = f"role-{uuid.uuid4()}"
                fhir_role = create_practitioner_role_fhir(
                    id=role_fhir_id,
                    practitioner_id=uploaded_fhir_id,
                    organization_id=organization.fhir_id,
                )
                upload_fhir_resource(fhir_role)
        except Exception:
            uploaded_fhir_id = None

        doctor = Doctor(
            fhir_id=uploaded_fhir_id,
            user_id=user.id,
            organization_id=payload.organization_id if payload.role == UserRole.doctor else None,
        )
        session.add(doctor)

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        constraint = getattr(getattr(exc, "orig", None), "diag", None)
        constraint_name = getattr(constraint, "constraint_name", None)
        msg = (
            "Email already registered"
            if constraint_name == "users_email_key"
            else f"Constraint violation ({constraint_name or exc.orig})"
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    session.refresh(user)

    # Create response with FHIR ID (only for doctors and practitioners)
    user_dict = {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "role": UserRole(user.role),
        "fhir_id": uploaded_fhir_id,
    }
    return UserRead.model_validate(user_dict)
