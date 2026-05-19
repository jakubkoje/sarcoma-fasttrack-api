import requests
import json

# FHIR Server Settings
FHIR_URL = "http://localhost:32783/csp/healthshare/demo/fhir/r4"
AUTH = ("_SYSTEM", "ISCDEMO")

def get_resource(resource_type, resource_id):
    """Retrieve a specific FHIR resource"""
    url = f"{FHIR_URL}/{resource_type}/{resource_id}"
    response = requests.get(url, auth=AUTH)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None

def search_resources(resource_type, params=None):
    """Search for FHIR resources"""
    url = f"{FHIR_URL}/{resource_type}"
    response = requests.get(url, auth=AUTH, params=params or {})
    
    if response.status_code == 200:
        return response.json()
    else:
        return None

def print_resource(resource_type, resource_id):
    """Print a resource in a readable format"""
    print(f"\n{'='*60}")
    print(f"{resource_type}/{resource_id}")
    print('='*60)
    
    resource = get_resource(resource_type, resource_id)
    if resource:
        print(json.dumps(resource, indent=2))
    else:
        print(f"❌ Not found")

def main():
    print("Retrieving all uploaded FHIR resources...\n")
    
    # Resources with known IDs
    print_resource("Organization", "org-1")
    print_resource("Practitioner", "prac-1")
    print_resource("PractitionerRole", "role-1")
    print_resource("Patient", "pat-1")
    print_resource("ServiceRequest", "rep-1")
    print_resource("DiagnosticReport", "exam-1")
    print_resource("ServiceRequest", "plan-1")
    
    # Resources without pre-assigned IDs (search for them)
    print(f"\n{'='*60}")
    print("FamilyMemberHistory (all)")
    print('='*60)
    fmh_bundle = search_resources("FamilyMemberHistory", {"patient": "Patient/pat-1"})
    if fmh_bundle and fmh_bundle.get('total', 0) > 0:
        for entry in fmh_bundle.get('entry', []):
            print(json.dumps(entry['resource'], indent=2))
    else:
        print("No FamilyMemberHistory found")
    
    print(f"\n{'='*60}")
    print("MedicationStatement (all)")
    print('='*60)
    ms_bundle = search_resources("MedicationStatement", {"patient": "Patient/pat-1"})
    if ms_bundle and ms_bundle.get('total', 0) > 0:
        for entry in ms_bundle.get('entry', []):
            print(json.dumps(entry['resource'], indent=2))
    else:
        print("No MedicationStatement found")
    
    print(f"\n{'='*60}")
    print("Observation (all)")
    print('='*60)
    obs_bundle = search_resources("Observation", {"patient": "Patient/pat-1"})
    if obs_bundle and obs_bundle.get('total', 0) > 0:
        for entry in obs_bundle.get('entry', []):
            print(json.dumps(entry['resource'], indent=2))
    else:
        print("No Observation found")
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"Organization: {get_resource('Organization', 'org-1') is not None}")
    print(f"Practitioner: {get_resource('Practitioner', 'prac-1') is not None}")
    print(f"PractitionerRole: {get_resource('PractitionerRole', 'role-1') is not None}")
    print(f"Patient: {get_resource('Patient', 'pat-1') is not None}")
    print(f"ServiceRequest (Report): {get_resource('ServiceRequest', 'rep-1') is not None}")
    print(f"DiagnosticReport: {get_resource('DiagnosticReport', 'exam-1') is not None}")
    print(f"ServiceRequest (Planned): {get_resource('ServiceRequest', 'plan-1') is not None}")
    
    fmh_count = search_resources("FamilyMemberHistory", {"patient": "Patient/pat-1"}).get('total', 0) if search_resources("FamilyMemberHistory", {"patient": "Patient/pat-1"}) else 0
    ms_count = search_resources("MedicationStatement", {"patient": "Patient/pat-1"}).get('total', 0) if search_resources("MedicationStatement", {"patient": "Patient/pat-1"}) else 0
    obs_count = search_resources("Observation", {"patient": "Patient/pat-1"}).get('total', 0) if search_resources("Observation", {"patient": "Patient/pat-1"}) else 0
    
    print(f"FamilyMemberHistory: {fmh_count} found")
    print(f"MedicationStatement: {ms_count} found")
    print(f"Observation: {obs_count} found")

if __name__ == "__main__":
    main()
