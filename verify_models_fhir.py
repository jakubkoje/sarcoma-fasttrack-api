from sqlalchemy import create_engine
from app.models.base import Base
from app.models.organization import Organization
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.report import Report
from app.models.examination import Examination, PlannedExamination

def verify_models():
    try:
        # Create an in-memory SQLite database
        engine = create_engine("sqlite:///:memory:")
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        print("Successfully created all tables.")
        
        # Verify table names
        expected_tables = {
            "organizations", "doctors", "patients", "reports", 
            "examinations", "planned_examinations"
        }
        created_tables = set(Base.metadata.tables.keys())
        
        if expected_tables.issubset(created_tables):
            print("All expected tables are present.")
        else:
            print(f"Missing tables: {expected_tables - created_tables}")
            exit(1)
            
        # Verify columns for Organization (should only have id and fhir_id)
        org_columns = {c.name for c in Organization.__table__.columns}
        if "name" in org_columns or "address" in org_columns:
             print("Error: Organization model still has clinical data fields.")
             exit(1)
        if "fhir_id" not in org_columns:
             print("Error: Organization model missing fhir_id.")
             exit(1)
             
        print("Model structure verification passed.")
            
    except Exception as e:
        print(f"Verification failed: {e}")
        exit(1)

if __name__ == "__main__":
    verify_models()
