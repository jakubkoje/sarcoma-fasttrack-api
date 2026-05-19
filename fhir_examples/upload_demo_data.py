import requests
from fhir_generators.resources import (
    create_patient,
    create_organization,
    create_practitioner,
    create_practitioner_role,
    create_service_request,
    create_family_member_history,
    create_medication_statement,
    create_observation_histology,
    create_diagnostic_report_exam,
    create_service_request_planned_exam
)
from datetime import datetime, timezone

# Helper to get current time with timezone
def now_aware():
    return datetime.now().astimezone()
import json

# FHIR Server Settings
FHIR_URL = "http://localhost:32783/csp/healthshare/demo/fhir/r4"
AUTH = ("_SYSTEM", "ISCDEMO")
HEADERS = {"Content-Type": "application/fhir+json"}

def upload_resource(resource):
    # fhir.resources models usually have resourceType field, or we can use class name
    try:
        resource_type = resource.resourceType
    except AttributeError:
        resource_type = resource.__class__.__name__
    resource_id = resource.id
    url = f"{FHIR_URL}/{resource_type}/{resource_id}"
    
    print(f"Uploading {resource_type}/{resource_id}...")
    
    # Use PUT to create/update with specific ID
    response = requests.put(
        url,
        data=resource.json(),
        auth=AUTH,
        headers=HEADERS
    )
    
    if response.status_code in [200, 201]:
        print(f"✅ Success: {response.status_code}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)

def main():
    print("Generating and Uploading Data to FHIR Server...\n")

    # 1. Organization
    org = create_organization(
        id="org-1",
        name="General Hospital",
        type_code="prov",
        address="123 Main St",
        contact="555-0100"
    )
    upload_resource(org)

    # 2. Practitioner
    practitioner = create_practitioner(id="prac-1", name="Dr. Alice Smith")
    upload_resource(practitioner)

    # 3. PractitionerRole
    role = create_practitioner_role(id="role-1", practitioner_id="prac-1", organization_id="org-1")
    upload_resource(role)

    # 4. Patient
    patient = create_patient(
        id="pat-1",
        first_name="John",
        last_name="Doe",
        address="456 Elm St",
        birth_number="800101/1234",
        phone="555-0200",
        email="john.doe@example.com",
        managing_org_id="org-1"
    )
    upload_resource(patient)

    # 5. ServiceRequest (Report)
    report = create_service_request(
        id="rep-1",
        patient_id="pat-1",
        doctor_id="prac-1",
        target_org_id="org-1",
        status="active",
        created_at=now_aware(),
        note="Patient complains of..."
    )
    upload_resource(report)

    # 6. Clinical Data
    fmh = create_family_member_history(patient_id="pat-1", note="Father had diabetes")
    upload_resource_generic(fmh)

    ms = create_medication_statement(patient_id="pat-1", medication_text="Aspirin")
    upload_resource_generic(ms)

    obs = create_observation_histology(
        patient_id="pat-1",
        service_request_id="rep-1",
        date=now_aware(),
        result="Benign tumor"
    )
    upload_resource_generic(obs)

    dr = create_diagnostic_report_exam(
        id="exam-1",
        patient_id="pat-1",
        service_request_id="rep-1",
        code="MRI Head",
        date=now_aware(),
        conclusion="Normal findings"
    )
    upload_resource(dr)

    planned_exam = create_service_request_planned_exam(
        id="plan-1",
        patient_id="pat-1",
        service_request_id="rep-1",
        code="CT Chest",
        note="Check for metastasis"
    )
    upload_resource(planned_exam)

def upload_resource_generic(resource):
    """Helper for resources without a pre-assigned ID (uses POST)"""
    try:
        resource_type = resource.resourceType
    except AttributeError:
        resource_type = resource.__class__.__name__
    url = f"{FHIR_URL}/{resource_type}"
    
    print(f"Uploading new {resource_type}...")
    
    response = requests.post(
        url,
        data=resource.json(),
        auth=AUTH,
        headers=HEADERS
    )
    
    if response.status_code in [200, 201]:
        try:
            resp_json = response.json()
            resource_id = resp_json.get('id')
            print(f"✅ Success: {response.status_code} (ID: {resource_id})")
        except Exception:
            # If no body, check Location header
            location = response.headers.get('Location')
            print(f"✅ Success: {response.status_code} (Location: {location})")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()
