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
from datetime import datetime
import json

def print_resource(resource):
    print(json.dumps(resource.dict(), indent=2, default=str))
    print("-" * 20)

def main():
    print("Testing FHIR Generators...\n")

    # 1. Organization
    org = create_organization(
        id="org-1",
        name="General Hospital",
        type_code="prov",
        address="123 Main St",
        contact="555-0100"
    )
    print("Organization:")
    print_resource(org)

    # 2. Practitioner
    practitioner = create_practitioner(id="prac-1", name="Dr. Alice Smith")
    print("Practitioner:")
    print_resource(practitioner)

    # 3. PractitionerRole
    role = create_practitioner_role(id="role-1", practitioner_id="prac-1", organization_id="org-1")
    print("PractitionerRole:")
    print_resource(role)

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
    print("Patient:")
    print_resource(patient)

    # 5. ServiceRequest (Report)
    report = create_service_request(
        id="rep-1",
        patient_id="pat-1",
        doctor_id="prac-1",
        target_org_id="org-1",
        status="active",
        created_at=datetime.now(),
        note="Patient complains of..."
    )
    print("ServiceRequest (Report):")
    print_resource(report)

    # 6. Clinical Data
    fmh = create_family_member_history(patient_id="pat-1", note="Father had diabetes")
    print("FamilyMemberHistory:")
    print_resource(fmh)

    ms = create_medication_statement(patient_id="pat-1", medication_text="Aspirin")
    print("MedicationStatement:")
    print_resource(ms)

    obs = create_observation_histology(
        patient_id="pat-1",
        service_request_id="rep-1",
        date=datetime.now(),
        result="Benign tumor"
    )
    print("Observation (Histology):")
    print_resource(obs)

    dr = create_diagnostic_report_exam(
        id="exam-1",
        patient_id="pat-1",
        service_request_id="rep-1",
        code="MRI Head",
        date=datetime.now(),
        conclusion="Normal findings"
    )
    print("DiagnosticReport (Past Exam):")
    print_resource(dr)

    planned_exam = create_service_request_planned_exam(
        id="plan-1",
        patient_id="pat-1",
        service_request_id="rep-1",
        code="CT Chest",
        note="Check for metastasis"
    )
    print("ServiceRequest (Planned Exam):")
    print_resource(planned_exam)

if __name__ == "__main__":
    main()
