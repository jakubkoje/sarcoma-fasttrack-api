#!/usr/bin/env python3
"""Fix specialist user by creating a Practitioner record"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from app.db.database_connection import create_database_engine
from app.models import User, Practitioner
import uuid
from app.core.config import settings
from app.services.fhir_client import create_practitioner_fhir, upload_fhir_resource

def main():
    engine = create_database_engine()
    
    with Session(engine) as session:
        # Find the specialist user
        specialist_user = session.exec(
            select(User).where(User.email == "praktik.kovarik@lekarna.cz")
        ).first()
        
        if not specialist_user:
            print("❌ Specialist user not found")
            return
        
        # Check if Practitioner already exists
        existing_practitioner = session.exec(
            select(Practitioner).where(Practitioner.user_id == specialist_user.id)
        ).first()
        
        if existing_practitioner:
            print(f"✅ Practitioner already exists for specialist user (ID: {existing_practitioner.id})")
            return
        
        print(f"Found specialist user: {specialist_user.email} (ID: {specialist_user.id})")
        
        # Generate FHIR ID
        fhir_id = f"prac-{uuid.uuid4()}"
        uploaded_fhir_id = None
        
        # Create FHIR Practitioner resource
        if settings.FHIR_ENABLED:
            try:
                fhir_practitioner = create_practitioner_fhir(
                    id=fhir_id,
                    name="MUDr. Marie Kováříková",
                    given_name="Marie",
                    family_name="Kováříková",
                )
                uploaded_fhir_id = upload_fhir_resource(fhir_practitioner)
                if uploaded_fhir_id:
                    print(f"✅ Created FHIR Practitioner: {uploaded_fhir_id}")
            except Exception as e:
                print(f"⚠️ Failed to create FHIR Practitioner: {e}")
        
        # Create Practitioner database record
        practitioner = Practitioner(
            fhir_id=uploaded_fhir_id or fhir_id,
            user_id=specialist_user.id,
            identifier_ico="12345678",
            given_name="Marie",
            family_name="Kováříková",
        )
        session.add(practitioner)
        session.commit()
        session.refresh(practitioner)
        
        print(f"✅ Created Practitioner record (ID: {practitioner.id}) for specialist user")
        print(f"   You can now use practitioner_id={practitioner.id} when creating reports")

if __name__ == "__main__":
    main()

