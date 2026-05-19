"""
Examples of adding custom parameters to FHIR resources using Extensions

FHIR Extensions allow you to add custom data that's not part of the standard spec.
"""

from fhir.resources.R4B.servicerequest import ServiceRequest
from fhir.resources.R4B.patient import Patient
from fhir.resources.R4B.reference import Reference
from fhir.resources.R4B.extension import Extension
from fhir.resources.R4B.codeableconcept import CodeableConcept
from fhir.resources.R4B.annotation import Annotation
from datetime import datetime

# ============================================================================
# Example 1: Add custom priority level to ServiceRequest
# ============================================================================

def create_service_request_with_custom_priority(
    id: str,
    patient_id: str,
    doctor_id: str,
    target_org_id: str,
    status: str,
    created_at: datetime,
    note: str = None,
    custom_priority: str = None,  # Custom parameter
    internal_notes: str = None     # Another custom parameter
):
    """
    Creates a ServiceRequest with custom extensions
    """
    sr = ServiceRequest(
        id=id,
        status=status,
        intent="order",
        subject=Reference(reference=f"Patient/{patient_id}")
    )
    
    sr.requester = Reference(reference=f"Practitioner/{doctor_id}")
    sr.performer = [Reference(reference=f"Organization/{target_org_id}")]
    sr.authoredOn = created_at
    
    if note:
        sr.note = [Annotation(text=note)]
    
    # Add custom extensions
    extensions = []
    
    # Extension 1: Custom priority
    if custom_priority:
        extensions.append(Extension(
            url="http://example.org/fhir/StructureDefinition/custom-priority",
            valueString=custom_priority
        ))
    
    # Extension 2: Internal notes (not visible to patient)
    if internal_notes:
        extensions.append(Extension(
            url="http://example.org/fhir/StructureDefinition/internal-notes",
            valueString=internal_notes
        ))
    
    if extensions:
        sr.extension = extensions
    
    return sr


# ============================================================================
# Example 2: Add custom fields to Patient
# ============================================================================

def create_patient_with_custom_fields(
    id: str,
    first_name: str,
    last_name: str,
    birth_number: str,
    # Custom parameters
    insurance_number: str = None,
    preferred_language: str = None,
    emergency_contact_name: str = None,
    emergency_contact_phone: str = None
):
    """
    Creates a Patient with custom extensions
    """
    from fhir.resources.R4B.humanname import HumanName
    from fhir.resources.R4B.identifier import Identifier
    
    patient = Patient(id=id)
    
    # Standard fields
    patient.name = [HumanName(given=[first_name], family=last_name)]
    patient.identifier = [Identifier(
        system="urn:oid:1.2.203.24341.1.1.1",
        value=birth_number
    )]
    
    # Add custom extensions
    extensions = []
    
    # Insurance number
    if insurance_number:
        extensions.append(Extension(
            url="http://example.org/fhir/StructureDefinition/insurance-number",
            valueString=insurance_number
        ))
    
    # Preferred language
    if preferred_language:
        extensions.append(Extension(
            url="http://example.org/fhir/StructureDefinition/preferred-language",
            valueCode=preferred_language
        ))
    
    # Emergency contact (complex extension with sub-extensions)
    if emergency_contact_name or emergency_contact_phone:
        emergency_ext = Extension(
            url="http://example.org/fhir/StructureDefinition/emergency-contact"
        )
        sub_extensions = []
        
        if emergency_contact_name:
            sub_extensions.append(Extension(
                url="name",
                valueString=emergency_contact_name
            ))
        
        if emergency_contact_phone:
            sub_extensions.append(Extension(
                url="phone",
                valueString=emergency_contact_phone
            ))
        
        emergency_ext.extension = sub_extensions
        extensions.append(emergency_ext)
    
    if extensions:
        patient.extension = extensions
    
    return patient


# ============================================================================
# Example 3: Add custom coded value
# ============================================================================

def create_service_request_with_custom_category(
    id: str,
    patient_id: str,
    doctor_id: str,
    status: str,
    custom_category: str = None  # e.g., "URGENT_ONCOLOGY", "ROUTINE_CHECKUP"
):
    """
    Add custom category using CodeableConcept extension
    """
    sr = ServiceRequest(
        id=id,
        status=status,
        intent="order",
        subject=Reference(reference=f"Patient/{patient_id}")
    )
    
    sr.requester = Reference(reference=f"Practitioner/{doctor_id}")
    
    # Add custom category as extension with CodeableConcept
    if custom_category:
        sr.extension = [Extension(
            url="http://example.org/fhir/StructureDefinition/request-category",
            valueCodeableConcept=CodeableConcept(
                text=custom_category,
                coding=[{
                    "system": "http://example.org/fhir/CodeSystem/request-categories",
                    "code": custom_category.upper().replace(" ", "_"),
                    "display": custom_category
                }]
            )
        )]
    
    return sr


# ============================================================================
# Example 4: Reading custom extensions
# ============================================================================

def get_custom_extension_value(resource, extension_url):
    """
    Helper function to read a custom extension value from a resource
    """
    if not hasattr(resource, 'extension') or not resource.extension:
        return None
    
    for ext in resource.extension:
        if ext.url == extension_url:
            # Return the value based on type
            if hasattr(ext, 'valueString'):
                return ext.valueString
            elif hasattr(ext, 'valueCode'):
                return ext.valueCode
            elif hasattr(ext, 'valueInteger'):
                return ext.valueInteger
            elif hasattr(ext, 'valueCodeableConcept'):
                return ext.valueCodeableConcept
            # Add more types as needed
    
    return None


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("FHIR Custom Parameters Examples\n")
    print("=" * 80)
    
    # Example 1: ServiceRequest with custom priority
    print("\n1. ServiceRequest with custom priority and internal notes:")
    print("-" * 80)
    
    sr = create_service_request_with_custom_priority(
        id="sr-custom-1",
        patient_id="pat-1",
        doctor_id="prac-1",
        target_org_id="org-1",
        status="active",
        created_at=datetime.now().astimezone(),
        note="Patient requires urgent consultation",
        custom_priority="CRITICAL",
        internal_notes="Patient has history of non-compliance"
    )
    
    print(sr.json(indent=2))
    
    # Example 2: Patient with custom fields
    print("\n\n2. Patient with insurance number and emergency contact:")
    print("-" * 80)
    
    patient = create_patient_with_custom_fields(
        id="pat-custom-1",
        first_name="Jane",
        last_name="Smith",
        birth_number="900202/5678",
        insurance_number="INS-123456",
        preferred_language="cs",
        emergency_contact_name="John Smith",
        emergency_contact_phone="+420 123 456 789"
    )
    
    print(patient.json(indent=2))
    
    # Example 3: ServiceRequest with custom category
    print("\n\n3. ServiceRequest with custom category:")
    print("-" * 80)
    
    sr_cat = create_service_request_with_custom_category(
        id="sr-cat-1",
        patient_id="pat-1",
        doctor_id="prac-1",
        status="active",
        custom_category="Urgent Oncology Referral"
    )
    
    print(sr_cat.json(indent=2))
    
    # Example 4: Reading custom extensions
    print("\n\n4. Reading custom extension values:")
    print("-" * 80)
    
    priority = get_custom_extension_value(
        sr,
        "http://example.org/fhir/StructureDefinition/custom-priority"
    )
    print(f"Custom Priority: {priority}")
    
    internal_notes = get_custom_extension_value(
        sr,
        "http://example.org/fhir/StructureDefinition/internal-notes"
    )
    print(f"Internal Notes: {internal_notes}")
    
    print("\n" + "=" * 80)
    print("✅ All examples complete!")
    print("\nKey Points:")
    print("  - Extensions use URLs to identify custom fields")
    print("  - You can use valueString, valueCode, valueInteger, etc.")
    print("  - Complex extensions can have nested sub-extensions")
    print("  - Extensions are preserved when stored in FHIR server")
