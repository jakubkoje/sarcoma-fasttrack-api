from typing import List
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.api.deps import require_user
from app.api.v1.endpoints.utils import ensure_found
from app.db.database_connection import get_session
from app.models import Report, Patient, Organization, User
from app.models.models import Doctor
from app.schemas.report import (
    ReportCreate,
    ReportRead,
    ReportStatus,
    ReportStatusUpdate,
)
from app.schemas.user import UserRole
from app.services.fhir_generators import (
    create_service_request as create_service_request_fhir,
)
from fhir.resources.R4B.extension import Extension
from fhir.resources.R4B.servicerequest import ServiceRequest
from app.services.fhir_client import upload_fhir_resource, get_fhir_resource
from app.services.fhir_extractors import extract_service_request_data
# from app.services.classification_service import classify_report
from app.services.vector_search_service import get_report_classification

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=List[ReportRead])
def list_reports(
    session: Session = Depends(get_session),
    user: User = Depends(require_user),
) -> List[ReportRead]:
    """List reports with data from database and optionally FHIR server."""
    query = select(Report)

    try:
        user_role = UserRole(user.role)
    except ValueError:
        user_role = None

    if user_role == UserRole.specialist:
        query = query.where(Report.status != ReportStatus.DRAFT.value)
    elif user_role == UserRole.doctor:
        doctor = session.exec(select(Doctor).where(Doctor.user_id == user.id)).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor profile not found for current user",
            )
        query = query.where(Report.doctor_id == doctor.id)

    reports = session.exec(query).all()
    result = []

    for report in reports:
        fhir_data = {"authored_on": None, "note": None}
        if report.fhir_id:
            fhir_resource = get_fhir_resource("ServiceRequest", report.fhir_id)
            if fhir_resource:
                fhir_data = extract_service_request_data(fhir_resource)

        report_dict = report.model_dump(exclude_none=True)
        status_val = report_dict.get("status")
        if status_val:
            try:
                status_enum = ReportStatus(status_val)
                report_dict["status"] = status_enum
                report_dict["status_cz"] = status_enum.cz
            except ValueError:
                report_dict["status_cz"] = status_val
        else:
            report_dict["status_cz"] = None
        report_dict.update(fhir_data)
        result.append(ReportRead.model_validate(report_dict))

    return result


@router.post("", response_model=ReportRead, status_code=201)
def create_report(
    payload: ReportCreate, session: Session = Depends(get_session)
) -> ReportRead:
    """
    Create report (ServiceRequest) and upload to FHIR server.

    This endpoint:
    1. Generates a unique FHIR ID
    2. Looks up Patient, Doctor, and Organization FHIR IDs
    3. Creates a FHIR ServiceRequest resource
    4. Uploads the resource to the FHIR server
    5. Stores the FHIR ID in the SQL database
    """
    # Look up related entities to get their FHIR IDs
    patient = session.get(Patient, payload.patient_id)
    ensure_found(bool(patient), "Patient")

    doctor_id_val = payload.doctor_id
    doctor = session.get(Doctor, doctor_id_val)
    ensure_found(bool(doctor), "Doctor")

    organization = session.get(Organization, payload.target_organization_id)
    ensure_found(bool(organization), "Organization")

    uploaded_fhir_id = None
    try:
        fhir_id = f"rep-{uuid.uuid4()}"
        status_upper = (
            (payload.status or ReportStatus.DRAFT).value
            if isinstance(payload.status, ReportStatus)
            else str(payload.status or "DRAFT").upper()
        )
        if status_upper == "DRAFT":
            fhir_status = "draft"
        elif status_upper == "ACTIVE":
            fhir_status = "active"
        else:
            fhir_status = "draft"
        raise Exception("fesbtrgiusb")
        fhir_service_request = create_service_request_fhir(
            id=fhir_id,
            patient_id=patient.fhir_id,
            doctor_id=doctor.fhir_id,  # Using practitioner as requester
            target_org_id=organization.fhir_id,
            status=fhir_status,
            created_at=datetime.now().astimezone(),  # Timezone-aware datetime for FHIR
            note=getattr(payload, "note", None),
            # Clinical information from payload
            is_new_patient=payload.is_new_patient,
            any_imaging_performed=payload.any_imaging_performed,
            additional_imaging_planned=payload.additional_imaging_planned,
            additional_imaging_note=payload.additional_imaging_note,
            anamnesis=payload.anamnesis,
            mkn10_code=payload.mkn10_code,
            family_history=payload.family_history,
            anticoagulant_medication=payload.anticoagulant_medication,
            anticoagulant_detail=payload.anticoagulant_detail,
            histology_performed=payload.histology_performed,
            histology_date=payload.histology_date,
            histology_result=payload.histology_result,
            summary=payload.summary,
            feedback_specialist=payload.feedback_specialist,
            attachment_path=payload.attachment_path,
        )
        uploaded_fhir_id = upload_fhir_resource(fhir_service_request)
    except Exception:
        uploaded_fhir_id = None

    # Create SQL record with FHIR ID
    print(uploaded_fhir_id)
    report_data = payload.model_dump(exclude={"status", "fhir_id"})
    report_data.pop("practitioner_id", None)
    report_data.pop("doctor_id", None)
    report = Report(
        fhir_id=uploaded_fhir_id,
        status=status_upper,
        doctor_id=doctor_id_val,
        **report_data,
    )
    session.add(report)
    print(report_data)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        constraint = getattr(getattr(exc, "orig", None), "diag", None)
        cname = getattr(constraint, "constraint_name", None)
        msg = f"Constraint violation ({cname or exc.orig})"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    session.refresh(report)

    # Classify the report using vector search
    classification = {}
    try:
        # Extract report data for classification
        report_data = report.model_dump()
        # classification = classify_report(
        #     report_id=report.id, report_data=report_data, fhir_id=uploaded_fhir_id
        # )

        # Update FHIR resource with classification
        try:
            raise Exception("fniedsbtrie")
            base_url = "http://terminology.hl7.org/CodeSystem"
            new_extensions = []

            # Helper to add extension
            def add_ext(key, val, is_float=False, is_int=False):
                if val is not None:
                    ext = Extension(url=f"{base_url}/{key.replace('_', '-')}")
                    if is_float:
                        ext.valueDecimal = val
                    elif is_int:
                        ext.valueInteger = val
                    else:
                        ext.valueString = str(val)
                    new_extensions.append(ext)

            add_ext("specialist", classification.get("specialist"))
            add_ext(
                "specialist_confidence",
                classification.get("specialist_confidence"),
                is_float=True,
            )
            add_ext("severity", classification.get("severity"))
            add_ext("severity_code", classification.get("severity_code"), is_int=True)
            add_ext(
                "severity_confidence",
                classification.get("severity_confidence"),
                is_float=True,
            )
            add_ext(
                "overall_confidence",
                classification.get("overall_confidence"),
                is_float=True,
            )

            if new_extensions:
                if fhir_service_request.extension is None:
                    fhir_service_request.extension = []
                fhir_service_request.extension.extend(new_extensions)

                import logging

                logger = logging.getLogger(__name__)
                logger.info(
                    f"Updating FHIR resource {uploaded_fhir_id} with {len(new_extensions)} new extensions"
                )
                logger.info(f"Extensions: {[e.url for e in new_extensions]}")

                upload_result = upload_fhir_resource(fhir_service_request)
                logger.info(f"Re-upload result: {upload_result}")
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(
                f"Failed to update FHIR with classification: {e}"
            )

    except Exception as e:
        # Log error but don't fail the request
        import logging

        logging.getLogger(__name__).error(f"Classification failed: {e}")

    # Merge report data with classification results
    report_dict = report.model_dump()
    status_val = report_dict.get("status")
    if status_val:
        try:
            status_enum = ReportStatus(status_val)
            report_dict["status"] = status_enum
            report_dict["status_cz"] = status_enum.cz
        except ValueError:
            report_dict["status_cz"] = status_val
    else:
        report_dict["status_cz"] = None
    report_dict.update(classification)

    return ReportRead.model_validate(report_dict)


@router.get("/{report_id}", response_model=ReportRead)
def get_report(report_id: int, session: Session = Depends(get_session)) -> ReportRead:
    """Get report detail with data from database and FHIR server."""
    report = session.get(Report, report_id)
    ensure_found(bool(report), "Report")

    fhir_data = {"authored_on": None, "note": None}
    if report.fhir_id:
        fhir_resource = get_fhir_resource("ServiceRequest", report.fhir_id)
        if fhir_resource:
            fhir_data = extract_service_request_data(fhir_resource)

    report_dict = report.model_dump(exclude_none=True)
    status_val = report_dict.get("status")
    if status_val:
        try:
            status_enum = ReportStatus(status_val)
            report_dict["status"] = status_enum
            report_dict["status_cz"] = status_enum.cz
        except ValueError:
            report_dict["status_cz"] = status_val
    else:
        report_dict["status_cz"] = None
    report_dict.update(fhir_data)
    return ReportRead.model_validate(report_dict)


# @router.patch("/{report_id}/status", response_model=ReportRead)
# def update_report_status(
#     report_id: int,
#     new_status: ReportStatus = Body(..., embed=True),
#     payload: ReportCreate = Body(None),
#     session: Session = Depends(get_session),
# ) -> ReportRead:
#     """Update report status with allowed transitions DRAFT -> ACTIVE -> SUBMITTED."""
#     report = session.get(Report, report_id)
#     ensure_found(bool(report), "Report")

#     current = (report.status or "").upper()
#     try:
#         current_enum = ReportStatus(current)
#     except ValueError:
#         current_enum = ReportStatus.DRAFT

#     allowed = {
#         ReportStatus.DRAFT: ReportStatus.ACTIVE,
#         ReportStatus.ACTIVE: ReportStatus.SUBMITTED,
#     }
#     if allowed.get(current_enum) != new_status:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Invalid transition {current_enum.value} -> {new_status.value}",
#         )

#     # If transitioning to ACTIVE and payload provided, update additional fields
#     if current_enum == ReportStatus.DRAFT and new_status == ReportStatus.ACTIVE and payload:
#         update_data = payload.model_dump(exclude_none=True)
#         for field, value in update_data.items():
#             if field in {"status", "fhir_id"}:
#                 continue
#             setattr(report, field, value)

#     report.status = new_status.value
#     session.add(report)
#     session.commit()
#     session.refresh(report)

#     report_dict = report.model_dump(exclude_none=True)
#     report_dict["status"] = new_status
#     report_dict["status_cz"] = new_status.cz
#     return ReportRead.model_validate(report_dict)


@router.patch("/{report_id}/feedback", response_model=ReportRead)
def update_report_feedback(
    report_id: int,
    feedback_specialist: str = Body(..., embed=True),
    session: Session = Depends(get_session),
) -> ReportRead:
    """Update specialist feedback text."""
    report = session.get(Report, report_id)
    ensure_found(bool(report), "Report")
    report.feedback_specialist = feedback_specialist
    session.add(report)
    session.commit()
    session.refresh(report)

    report_dict = report.model_dump(exclude_none=True)
    status_val = report_dict.get("status")
    if status_val:
        try:
            status_enum = ReportStatus(status_val)
            report_dict["status"] = status_enum
            report_dict["status_cz"] = status_enum.cz
        except ValueError:
            report_dict["status_cz"] = status_val
    else:
        report_dict["status_cz"] = None
    return ReportRead.model_validate(report_dict)


@router.get("/{report_id}/classification")
def get_classification(report_id: int, session: Session = Depends(get_session)) -> dict:
    """
    Get classification results for a report.

    Returns specialist type, severity level, and confidence scores.
    """
    report = session.get(Report, report_id)
    ensure_found(bool(report), "Report")

    # Try to get stored classification from IRIS
    classification = get_report_classification(report_id)

    if not classification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No classification found for this report. Try reclassifying.",
        )

    return classification


@router.post("/{report_id}/reclassify")
def reclassify_report(report_id: int, session: Session = Depends(get_session)) -> dict:
    """
    Manually trigger reclassification of a report.

    Useful if the report has been updated or if you want to
    regenerate the classification with updated training data.
    """
    report = session.get(Report, report_id)
    ensure_found(bool(report), "Report")

    # Extract report data and reclassify
    report_data = report.model_dump()
    # classification = classify_report(
    #     report_id=report.id, report_data=report_data, fhir_id=report.fhir_id
    # )
    classification = {}

    return classification


@router.patch("/{report_id}/status", response_model=ReportRead)
def update_report_status(
    report_id: int,
    payload: ReportStatusUpdate,
    session: Session = Depends(get_session),
) -> ReportRead:
    """
    Update the status of a report.

    Updates both the database record and the FHIR ServiceRequest resource
    if it exists. The status is synchronized between both systems.
    """
    # Get the report
    report = session.get(Report, report_id)
    ensure_found(bool(report), "Report")

    # Convert status to string for database
    new_status = payload.status.value

    # Update database record
    report.status = new_status
    session.add(report)
    session.commit()
    session.refresh(report)

    # Update FHIR resource if it exists
    if report.fhir_id:
        try:
            # Retrieve existing FHIR resource
            fhir_resource_dict = get_fhir_resource("ServiceRequest", report.fhir_id)
            if fhir_resource_dict:
                # Parse the FHIR resource
                fhir_service_request = ServiceRequest.parse_obj(fhir_resource_dict)

                # Map our status to FHIR status
                # FHIR ServiceRequest status values: draft, active, on-hold, revoked, completed, entered-in-error, unknown
                status_mapping = {
                    "DRAFT": "draft",
                    "ACTIVE": "active",
                    "SUBMITTED": "active",
                    "SENT": "active",
                    "DONE": "completed",
                    "ERROR": "entered-in-error",
                }
                fhir_status = status_mapping.get(new_status, "active")

                # Update the status
                fhir_service_request.status = fhir_status

                # Re-upload to FHIR server
                upload_fhir_resource(fhir_service_request)
        except Exception as e:
            # Log error but don't fail the request
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to update FHIR resource status: {e}")

    # Get updated report data with FHIR enrichment
    fhir_data = {"authored_on": None, "note": None}
    if report.fhir_id:
        fhir_resource = get_fhir_resource("ServiceRequest", report.fhir_id)
        if fhir_resource:
            fhir_data = extract_service_request_data(fhir_resource)

    # Build response
    report_dict = report.model_dump(exclude_none=True)
    status_val = report_dict.get("status")
    if status_val:
        try:
            status_enum = ReportStatus(status_val)
            report_dict["status"] = status_enum
            report_dict["status_cz"] = status_enum.cz
        except ValueError:
            report_dict["status_cz"] = status_val
    else:
        report_dict["status_cz"] = None

    report_dict.update(fhir_data)

    return ReportRead.model_validate(report_dict)
