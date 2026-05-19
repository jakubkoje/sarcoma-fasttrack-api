from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import require_user
from app.models import User

def mock_require_user():
    return User(id=1, email="test@example.com", is_active=True)

app.dependency_overrides[require_user] = mock_require_user

client = TestClient(app)

def test_list_reports():
    print("Testing GET /api/v1/reports...")
    response = client.get("/api/v1/reports")
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return
    
    data = response.json()
    print(f"Got {len(data)} reports")
    if not data:
        print("No reports found to verify fields.")
    
    print("Searching for report with valid names...")
    found = False
    for r in data:
        p_name = r.get('patient_name')
        o_name = r.get('organization_name')
        if p_name and p_name != "None None":
            print(f"Found report with patient name: {p_name}")
            found = True
        if o_name:
            print(f"Found report with organization name: {o_name}")
            found = True
        if found:
            break

    # Debug: check patients
    print("\nChecking Patients directly...")
    from app.db.database_connection import get_session
    from app.models import Patient
    from sqlmodel import select
    
    # We need a session. Since we are outside of dependency injection, we create one manually.
    # But get_session is a generator.
    gen = get_session()
    session = next(gen)
    try:
        patients = session.exec(select(Patient)).all()
        print(f"Found {len(patients)} patients.")
        for p in patients[:5]:
            print(f"Patient ID {p.id}: {p.given_name} {p.family_name}")
    finally:
        session.close()

if __name__ == "__main__":
    test_list_reports()
