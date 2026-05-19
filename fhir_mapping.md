# FHIR Mapping for SarcomFasttrack (FHIR-First Architecture)

In this architecture, the SQL database is a thin layer used primarily for relational linking and process management. **All clinical and demographic data is stored in the FHIR server.** The SQL tables store references (`fhir_id`) to the corresponding FHIR resources.

## 1. Patient
Maps to `Patient` resource.

| SQL Field | FHIR Path | Note |
|---|---|---|
| `fhir_id` | `Patient.id` | The logical ID of the resource on the FHIR server. |
| - | `Patient.name.given` | First Name |
| - | `Patient.name.family` | Last Name |
| - | `Patient.address.text` | Address |
| - | `Patient.identifier` | Birth Number (RČ). System: `urn:oid:1.2.203.24341.1.1.1` |
| - | `Patient.telecom` | Phone and Email |
| - | `Patient.managingOrganization` | Insurance Company (Reference to Organization) |

## 2. Doctor
Maps to `Practitioner` resource.

| SQL Field | FHIR Path | Note |
|---|---|---|
| `fhir_id` | `Practitioner.id` | |
| - | `Practitioner.name.text` | Name |
| `organization_id` | `PractitionerRole.organization` | Link to Organization resource |

## 3. Organization
Maps to `Organization` resource.

| SQL Field | FHIR Path | Note |
|---|---|---|
| `fhir_id` | `Organization.id` | |
| - | `Organization.name` | Name |
| - | `Organization.type` | Type |
| - | `Organization.address` | Address |
| - | `Organization.telecom` | Contact Info |

## 4. Report (Referral)
Maps to `ServiceRequest` resource.

| SQL Field | FHIR Path | Note |
|---|---|---|
| `fhir_id` | `ServiceRequest.id` | |
| `patient_id` | `ServiceRequest.subject` | Reference(Patient) |
| `doctor_id` | `ServiceRequest.requester` | Reference(Practitioner) |
| `target_organization_id` | `ServiceRequest.performer` | Reference(Organization) |
| `status` | `ServiceRequest.status` | `draft` or `active` |
| - | `ServiceRequest.authoredOn` | Created At |
| - | `ServiceRequest.note` | Summary |

## 5. Clinical Data (Anamnesis & Findings)
All stored as FHIR resources linked to the `ServiceRequest` (Report).

### Family Predisposition
Maps to `FamilyMemberHistory`.
- `patient`: Reference(Patient)
- `note`: Text description

### Blood Thinners
Maps to `MedicationStatement`.
- `status`: `active`
- `medicationCodeableConcept.text`: Details of medication
- `subject`: Reference(Patient)

### Histology
Maps to `Observation` or `DiagnosticReport`.
- `code`: LOINC code for Histology.
- `effectiveDateTime`: Date
- `valueString`: Result
- `subject`: Reference(Patient)
- `basedOn`: Reference(ServiceRequest)

### Examinations (Imaging)
Maps to `DiagnosticReport` (for past exams) or `ServiceRequest` (for planned exams).

**Past Examinations:**
- `id`: Stored in `examinations.fhir_id`
- `status`: `final`
- `code`: LOINC/SNOMED code for the modality (MRI, CT, etc.)
- `effectiveDateTime`: Date
- `conclusion`: Description
- `basedOn`: Reference(ServiceRequest)

**Planned Examinations:**
- `id`: Stored in `planned_examinations.fhir_id`
- `status`: `active`
- `intent`: `plan`
- `code`: LOINC/SNOMED code for the modality.
- `note`: Note
- `basedOn`: Reference(ServiceRequest)
