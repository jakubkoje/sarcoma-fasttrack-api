"""
Example: Using custom extensions with your FHIR generators

This shows how to add custom parameters to ServiceRequest using the updated generator
"""

from fhir_generators.resources import create_service_request
from fhir.resources.R4B.extension import Extension
from datetime import datetime

# Example 1: ServiceRequest with custom priority
print("Example 1: ServiceRequest with custom priority")
print("=" * 80)

report = create_service_request(
    id="rep-custom-1",
    patient_id="pat-1",
    doctor_id="prac-1",
    target_org_id="org-1",
    status="active",
    created_at=datetime.now().astimezone(),
    note="Patient complains of persistent headaches",
    extensions=[
        Extension(
            url="http://sarcomfasttrack.org/fhir/priority",
            valueString="URGENT"
        ),
        Extension(
            url="http://sarcomfasttrack.org/fhir/internal-notes",
            valueString="Patient requires immediate attention"
        )
    ]
)

print(report.json(indent=2))

# Example 2: ServiceRequest with custom category and referral source
print("\n\nExample 2: ServiceRequest with custom category and referral source")
print("=" * 80)

from fhir.resources.R4B.codeableconcept import CodeableConcept

report2 = create_service_request(
    id="rep-custom-2",
    patient_id="pat-1",
    doctor_id="prac-1",
    target_org_id="org-1",
    status="active",
    created_at=datetime.now().astimezone(),
    note="Suspected sarcoma - requires specialist evaluation",
    extensions=[
        Extension(
            url="http://sarcomfasttrack.org/fhir/referral-category",
            valueCodeableConcept=CodeableConcept(
                text="Oncology - Sarcoma",
                coding=[{
                    "system": "http://sarcomfasttrack.org/fhir/categories",
                    "code": "ONCOLOGY_SARCOMA",
                    "display": "Oncology - Sarcoma"
                }]
            )
        ),
        Extension(
            url="http://sarcomfasttrack.org/fhir/referral-source",
            valueString="GP Clinic - Prague 1"
        ),
        Extension(
            url="http://sarcomfasttrack.org/fhir/expected-turnaround-days",
            valueInteger=7
        )
    ]
)

print(report2.json(indent=2))

# Example 3: Upload to FHIR server
print("\n\nExample 3: Uploading to FHIR server")
print("=" * 80)

import requests

FHIR_URL = "http://localhost:32783/csp/healthshare/demo/fhir/r4"
AUTH = ("_SYSTEM", "ISCDEMO")
HEADERS = {"Content-Type": "application/fhir+json"}

url = f"{FHIR_URL}/ServiceRequest/{report.id}"
response = requests.put(
    url,
    data=report.json(),
    auth=AUTH,
    headers=HEADERS
)

if response.status_code in [200, 201]:
    print(f"✅ ServiceRequest uploaded successfully!")
    print(f"   ID: {report.id}")
    print(f"   URL: {url}")
    print(f"\n   Custom extensions preserved:")
    print(f"   - Priority: URGENT")
    print(f"   - Internal notes: Patient requires immediate attention")
else:
    print(f"❌ Upload failed: {response.status_code}")
    print(response.text)

# Example 4: Retrieve and read custom extensions
print("\n\nExample 4: Retrieving and reading custom extensions")
print("=" * 80)

# Retrieve the resource
response = requests.get(url, auth=AUTH)

if response.status_code == 200:
    retrieved = response.json()
    
    print("Retrieved resource with extensions:")
    
    if 'extension' in retrieved:
        for ext in retrieved['extension']:
            print(f"\n  Extension URL: {ext['url']}")
            
            # Get the value (could be valueString, valueInteger, etc.)
            for key, value in ext.items():
                if key.startswith('value'):
                    print(f"  Value ({key}): {value}")
    else:
        print("  No extensions found")

print("\n" + "=" * 80)
print("✅ Examples complete!")
print("\nKey takeaways:")
print("  1. Use Extension objects to add custom fields")
print("  2. Extensions are preserved when stored in FHIR server")
print("  3. You can use different value types: valueString, valueInteger, valueCodeableConcept, etc.")
print("  4. Use meaningful URLs to identify your custom fields")
