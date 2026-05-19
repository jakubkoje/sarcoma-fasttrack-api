"""
FHIR Resource Generator Functions
Updated to match current schema structure
"""
from fhir.resources.R4B.patient import Patient
from fhir.resources.R4B.organization import Organization
from fhir.resources.R4B.practitioner import Practitioner
from fhir.resources.R4B.practitionerrole import PractitionerRole
from fhir.resources.R4B.servicerequest import ServiceRequest
from fhir.resources.R4B.humanname import HumanName
from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.contactpoint import ContactPoint
from fhir.resources.R4B.address import Address
from fhir.resources.R4B.reference import Reference
from fhir.resources.R4B.codeableconcept import CodeableConcept
from fhir.resources.R4B.annotation import Annotation
from fhir.resources.R4B.coding import Coding
from datetime import datetime, date
from typing import Optional


def create_patient(
    id: str,
    first_name: str = None,
    last_name: str = None,
    given_name: str = None,
    family_name: str = None,
    address: str = None,
    address_text: str = None,
    address_city: str = None,
    address_postal_code: str = None,
    address_country: str = None,
    birth_number: str = None,
    identifier_rc: str = None,
    phone: str = None,
    email: Optional[str] = None,
    birth_date: Optional[date] = None,
    gender: Optional[str] = None,
    insurance_company_code: Optional[str] = None,
    managing_org_id: Optional[str] = None
) -> Patient:
    """
    Create a FHIR Patient resource
    Supports both legacy (first_name/last_name) and new (given_name/family_name) fields
    """
    patient = Patient(id=id)
    
    # Name - use new fields if available, fallback to legacy
    given = given_name or first_name
    family = family_name or last_name
    if given or family:
        patient.name = [HumanName(given=[given] if given else None, family=family)]
    
    # Identifier (Birth Number - RČ)
    identifiers = []
    rc = identifier_rc or birth_number
    if rc:
        identifiers.append(Identifier(
            system="urn:oid:1.2.203.24341.1.1.1",
            value=rc,
            type=CodeableConcept(
                coding=[Coding(
                    system="http://terminology.hl7.org/CodeSystem/v2-0203",
                    code="NI",
                    display="National unique individual identifier"
                )]
            )
        ))
    
    # Insurance company code
    if insurance_company_code:
        identifiers.append(Identifier(
            system="urn:oid:1.2.203.24341.1.1.2",
            value=insurance_company_code,
            type=CodeableConcept(
                coding=[Coding(
                    system="http://terminology.hl7.org/CodeSystem/v2-0203",
                    code="MB",
                    display="Member Number"
                )]
            )
        ))
    
    if identifiers:
        patient.identifier = identifiers
    
    # Address - use structured if available, fallback to text
    addr_text = address_text or address
    if addr_text or address_city or address_postal_code or address_country:
        patient.address = [Address(
            text=addr_text,
            city=address_city,
            postalCode=address_postal_code,
            country=address_country
        )]
    
    # Telecom (phone and email)
    telecom = []
    if phone:
        telecom.append(ContactPoint(system="phone", value=phone))
    if email:
        telecom.append(ContactPoint(system="email", value=email))
    if telecom:
        patient.telecom = telecom
    
    # Birth date
    if birth_date:
        patient.birthDate = birth_date
    
    # Gender
    if gender:
        patient.gender = gender.lower()
    
    # Managing Organization (Insurance Company)
    if managing_org_id:
        patient.managingOrganization = Reference(reference=f"Organization/{managing_org_id}")
    
    return patient


def create_organization(
    id: str,
    name: str,
    type_code: str = "prov",
    address: str = None,
    address_line: str = None,
    address_city: str = None,
    address_postal_code: str = None,
    address_country: str = None,
    contact: str = None,
    phone: str = None,
    email: Optional[str] = None,
    ico: Optional[str] = None,
    dic: Optional[str] = None
) -> Organization:
    """
    Create a FHIR Organization resource
    Supports structured address and multiple identifiers
    """
    org = Organization(id=id, name=name)
    
    # Type
    org.type = [CodeableConcept(
        coding=[Coding(
            system="http://terminology.hl7.org/CodeSystem/organization-type",
            code=type_code
        )]
    )]
    
    # Identifiers (IČO, DIČ)
    identifiers = []
    if ico:
        identifiers.append(Identifier(
            system="urn:oid:1.2.203.24341.1.1.3",
            value=ico,
            type=CodeableConcept(text="IČO")
        ))
    if dic:
        identifiers.append(Identifier(
            system="urn:oid:1.2.203.24341.1.1.4",
            value=dic,
            type=CodeableConcept(text="DIČ")
        ))
    if identifiers:
        org.identifier = identifiers
    
    # Address - use structured if available, fallback to text
    addr_text = address_line or address
    if addr_text or address_city or address_postal_code or address_country:
        org.address = [Address(
            text=addr_text,
            city=address_city,
            postalCode=address_postal_code,
            country=address_country
        )]
    
    # Telecom (phone and email)
    telecom = []
    contact_phone = phone or contact
    if contact_phone:
        telecom.append(ContactPoint(system="phone", value=contact_phone))
    if email:
        telecom.append(ContactPoint(system="email", value=email))
    if telecom:
        org.telecom = telecom
    
    return org


def create_practitioner(
    id: str,
    name: str = None,
    family_name: str = None,
    given_name: str = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    identifier_ico: Optional[str] = None
) -> Practitioner:
    """
    Create a FHIR Practitioner resource
    Supports structured name and contact info
    """
    practitioner = Practitioner(id=id)
    
    # Name - use structured if available, fallback to text
    if given_name or family_name:
        practitioner.name = [HumanName(given=[given_name] if given_name else None, family=family_name)]
    elif name:
        practitioner.name = [HumanName(text=name)]
    
    # Identifier (IČO)
    if identifier_ico:
        practitioner.identifier = [Identifier(
            system="urn:oid:1.2.203.24341.1.1.3",
            value=identifier_ico,
            type=CodeableConcept(text="IČO")
        )]
    
    # Telecom
    telecom = []
    if phone:
        telecom.append(ContactPoint(system="phone", value=phone))
    if email:
        telecom.append(ContactPoint(system="email", value=email))
    if telecom:
        practitioner.telecom = telecom
    
    return practitioner


def create_practitioner_role(
    id: str,
    practitioner_id: str,
    organization_id: str,
    specialty_code: Optional[str] = None,
    role_code: Optional[str] = None
) -> PractitionerRole:
    """
    Create a FHIR PractitionerRole resource
    Supports specialty and role codes
    """
    role = PractitionerRole(id=id)
    role.practitioner = Reference(reference=f"Practitioner/{practitioner_id}")
    role.organization = Reference(reference=f"Organization/{organization_id}")
    
    # Specialty
    if specialty_code:
        role.specialty = [CodeableConcept(
            coding=[Coding(
                system="http://snomed.info/sct",
                code=specialty_code
            )]
        )]
    
    # Role
    if role_code:
        role.code = [CodeableConcept(
            coding=[Coding(
                system="http://terminology.hl7.org/CodeSystem/practitioner-role",
                code=role_code
            )]
        )]
    
    return role


def create_service_request(
    id: str,
    patient_id: str,
    doctor_id: str,
    target_org_id: str,
    status: str = "active",
    created_at: Optional[datetime] = None,
    note: Optional[str] = None,
    # Clinical information fields from ReportBase
    is_new_patient: Optional[bool] = None,
    any_imaging_performed: Optional[bool] = None,
    additional_imaging_planned: Optional[bool] = None,
    additional_imaging_note: Optional[str] = None,
    anamnesis: Optional[str] = None,
    mkn10_code: Optional[str] = None,
    family_history: Optional[str] = None,
    anticoagulant_medication: Optional[bool] = None,
    anticoagulant_detail: Optional[str] = None,
    histology_performed: Optional[bool] = None,
    histology_date: Optional[date] = None,
    histology_result: Optional[str] = None,
    summary: Optional[str] = None,
    feedback_specialist: Optional[str] = None,
    attachment_path: Optional[str] = None
) -> ServiceRequest:
    """
    Create a FHIR ServiceRequest resource (represents a Report/Referral)
    Stores all clinical information as structured FHIR extensions
    """
    from fhir.resources.R4B.extension import Extension
    
    sr = ServiceRequest(
        id=id,
        status=status.lower() if status else "draft",
        intent="order",
        subject=Reference(reference=f"Patient/{patient_id}")
    )
    
    sr.requester = Reference(reference=f"Practitioner/{doctor_id}")
    sr.performer = [Reference(reference=f"Organization/{target_org_id}")]
    
    if created_at:
        sr.authoredOn = created_at
    
    # Add diagnosis code (MKN-10) as reasonCode
    if mkn10_code:
        sr.reasonCode = [CodeableConcept(
            coding=[Coding(
                system="http://hl7.org/fhir/sid/icd-10",
                code=mkn10_code,
                display=f"ICD-10: {mkn10_code}"
            )],
            text=f"MKN-10: {mkn10_code}"
        )]
    
    # Create structured extensions for all clinical data
    extensions = []
    base_url = "http://terminology.hl7.org/CodeSystem"
    
    # Patient status
    if is_new_patient is not None:
        extensions.append(Extension(
            url=f"{base_url}/is-new-patient",
            valueBoolean=is_new_patient
        ))
    
    # Anamnesis
    if anamnesis:
        extensions.append(Extension(
            url=f"{base_url}/anamnesis",
            valueString=anamnesis
        ))
    
    # Family history
    if family_history:
        extensions.append(Extension(
            url=f"{base_url}/family-history",
            valueString=family_history
        ))
    
    # Imaging information
    if any_imaging_performed is not None:
        extensions.append(Extension(
            url=f"{base_url}/any-imaging-performed",
            valueBoolean=any_imaging_performed
        ))
    
    if additional_imaging_planned is not None:
        extensions.append(Extension(
            url=f"{base_url}/additional-imaging-planned",
            valueBoolean=additional_imaging_planned
        ))
    
    if additional_imaging_note:
        extensions.append(Extension(
            url=f"{base_url}/additional-imaging-note",
            valueString=additional_imaging_note
        ))
    
    # Anticoagulant information
    if anticoagulant_medication is not None:
        extensions.append(Extension(
            url=f"{base_url}/anticoagulant-medication",
            valueBoolean=anticoagulant_medication
        ))
    
    if anticoagulant_detail:
        extensions.append(Extension(
            url=f"{base_url}/anticoagulant-detail",
            valueString=anticoagulant_detail
        ))
    
    # Histology information
    if histology_performed is not None:
        extensions.append(Extension(
            url=f"{base_url}/histology-performed",
            valueBoolean=histology_performed
        ))
    
    if histology_date:
        extensions.append(Extension(
            url=f"{base_url}/histology-date",
            valueDate=histology_date
        ))
    
    if histology_result:
        extensions.append(Extension(
            url=f"{base_url}/histology-result",
            valueString=histology_result
        ))
    
    # Summary
    if summary:
        extensions.append(Extension(
            url=f"{base_url}/summary",
            valueString=summary
        ))
    
    # Feedback from specialist
    if feedback_specialist:
        extensions.append(Extension(
            url=f"{base_url}/feedback-specialist",
            valueString=feedback_specialist
        ))
    
    # Attachment reference
    if attachment_path:
        extensions.append(Extension(
            url=f"{base_url}/attachment-path",
            valueString=attachment_path
        ))
    
    # Add all extensions to the ServiceRequest
    if extensions:
        sr.extension = extensions
    
    # Add note as annotation if provided
    if note:
        sr.note = [Annotation(text=note)]
    
    return sr
