"""
Database Seeder Script
Seeds PostgreSQL database with sample data and creates corresponding FHIR resources.

Environment Variables:
    SEED_ORGANIZATIONS=true/false - Enable/disable seeding organizations (default: true)
    SEED_USERS=true/false - Enable/disable seeding users (default: true)
    SEED_PATIENTS=true/false - Enable/disable seeding patients (default: true)
    SEED_REPORTS=true/false - Enable/disable seeding reports (default: true)
    SEED_DATA_FILE=path/to/seed_data.json - Optional JSON file with custom seed data
    SEED_OVERWRITE=true/false - Overwrite existing data (default: false)
"""

import sys
import os
import json
from pathlib import Path
from datetime import date, datetime
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, create_engine, SQLModel, select
from app.core.config import settings
from app.core.security import generate_salt, hash_password
from app.models import (
    Organization,
    User,
    Doctor,
    Practitioner,
    Patient,
    Report,
    MKN10,
)
from app.services.fhir_generators import (
    create_organization as create_org_fhir,
    create_practitioner as create_practitioner_fhir,
    create_practitioner_role as create_role_fhir,
    create_patient as create_patient_fhir,
    create_service_request as create_service_request_fhir,
)
from app.services.fhir_client import upload_fhir_resource
import uuid
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_env_bool(key: str, default: bool = True) -> bool:
    """Get boolean from environment variable"""
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def load_seed_data_from_file(file_path: str) -> Optional[dict]:
    """Load seed data from JSON file if provided"""
    if not file_path or not os.path.exists(file_path):
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.info(f"✅ Loaded seed data from {file_path}")
            return data
    except Exception as e:
        logger.warning(f"⚠️ Failed to load seed data from {file_path}: {e}")
        return None


def get_seed_data() -> dict:
    """Get seed data from environment variables or use defaults"""
    seed_data_file = os.getenv("SEED_DATA_FILE")
    custom_data = load_seed_data_from_file(seed_data_file) if seed_data_file else None

    if custom_data:
        return custom_data

    # Default seed data
    return {
        "organizations": [
            {
                "name": "Fakultní nemocnice Brno",
                "type_code": "prov",
                "address_line": "Jihlavská 20",
                "address_city": "Brno",
                "address_postal_code": "625 00",
                "address_country": "CZ",
                "phone": "+420532231111",
                "email": "info@fnbrno.cz",
                "ico": "00169801",
                "dic": "CZ00169801",
            },
            {
                "name": "Nemocnice u sv. Anny v Brně",
                "type_code": "prov",
                "address_line": "Pekařská 53",
                "address_city": "Brno",
                "address_postal_code": "656 91",
                "address_country": "CZ",
                "phone": "+420543181111",
                "email": "info@fnusa.cz",
                "ico": "00169802",
            },
            {
                "name": "VZP - Všeobecná zdravotní pojišťovna",
                "type_code": "ins",
                "address_line": "Moskevská 15",
                "address_city": "Praha",
                "address_postal_code": "101 00",
                "address_country": "CZ",
                "phone": "+420257041111",
                "email": "info@vzp.cz",
                "ico": "00169803",
            },
        ],
        "users": [
            {
                "email": "doktor.novak@fnbrno.cz",
                "password": "doctor123",
                "role": "doctor",
                "practitioner_name": "MUDr. Jan Novák",
                "given_name": "Jan",
                "family_name": "Novák",
                "organization": "Fakultní nemocnice Brno",
            },
            {
                "email": "doktor.svoboda@fnbrno.cz",
                "password": "doctor123",
                "role": "doctor",
                "practitioner_name": "MUDr. Petr Svoboda",
                "given_name": "Petr",
                "family_name": "Svoboda",
                "organization": "Fakultní nemocnice Brno",
            },
            {
                "email": "praktik.kovarik@lekarna.cz",
                "password": "practitioner123",
                "role": "specialist",
                "practitioner_name": "MUDr. Marie Kováříková",
                "given_name": "Marie",
                "family_name": "Kováříková",
                "ico": "12345678",
            },
            {
                "email": "koordinator@system.cz",
                "password": "coordinator123",
                "role": "admin",
            },
        ],
        "patients": [
            {
                "given_name": "Jan",
                "family_name": "Novák",
                "identifier_rc": "850101/1234",
                "birth_date": "1985-01-01",
                "gender": "male",
                "phone": "+420123456789",
                "email": "jan.novak@example.com",
                "address_text": "Hlavní 123",
                "address_city": "Brno",
                "address_postal_code": "602 00",
                "address_country": "CZ",
                "insurance_company_code": "211",
                "managing_organization": "VZP - Všeobecná zdravotní pojišťovna",
            },
            {
                "given_name": "Marie",
                "family_name": "Svobodová",
                "identifier_rc": "900202/5678",
                "birth_date": "1990-02-02",
                "gender": "female",
                "phone": "+420987654321",
                "email": "marie.svobodova@example.com",
                "address_text": "Vedlejší 456",
                "address_city": "Praha",
                "address_postal_code": "100 00",
                "address_country": "CZ",
            },
            {
                "given_name": "Petr",
                "family_name": "Dvořák",
                "identifier_rc": "880303/9012",
                "birth_date": "1988-03-03",
                "gender": "male",
                "phone": "+420555666777",
                "address_text": "Náměstí 789",
                "address_city": "Ostrava",
                "address_postal_code": "700 00",
                "address_country": "CZ",
            },
        ],
        "reports": [
            {
                "patient_index": 0,
                "doctor_email": "doktor.novak@fnbrno.cz",
                "target_organization": "Fakultní nemocnice Brno",
                "status": "DRAFT",
                "anamnesis": "Pacient si stěžuje na bolest v oblasti hrudníku.",
                "family_history": "Otec měl diabetes.",
                "any_imaging_performed": True,
                "additional_imaging_planned": True,
                "additional_imaging_note": "Doporučeno CT vyšetření.",
                "mkn10_code": "C49.3",
                "histology_performed": False,
                "summary": "Základní vyšetření provedeno.",
            },
            {
                "patient_index": 1,
                "doctor_email": "doktor.svoboda@fnbrno.cz",
                "target_organization": "Nemocnice u sv. Anny v Brně",
                "status": "ACTIVE",
                "anamnesis": "Pacientka s podezřením na sarkom.",
                "any_imaging_performed": True,
                "additional_imaging_planned": False,
                "mkn10_code": "C49.4",
                "histology_performed": True,
                "histology_date": "2024-01-15",
                "histology_result": "Benigní nádor.",
                "summary": "Vyšetření potvrdilo benigní charakter.",
            },
        ],
    }


def create_database_engine():
    """Create database engine with connection string"""
    from urllib.parse import quote_plus

    password = quote_plus(settings.DB_PASSWORD)
    database_url = (
        f"postgresql+psycopg://{settings.DB_USER}:{password}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )
    return create_engine(database_url, pool_pre_ping=True)


def create_tables(engine):
    """Create all database tables"""
    logger.info("Creating database tables...")
    SQLModel.metadata.create_all(engine)
    logger.info("✅ Database tables created")


def seed_organizations(
    session: Session, seed_data: dict, overwrite: bool = False
) -> dict:
    """Seed organizations and create FHIR Organization resources"""
    if not get_env_bool("SEED_ORGANIZATIONS", True):
        logger.info("⏭️ Skipping organizations (SEED_ORGANIZATIONS=false)")
        return {}

    logger.info("Seeding organizations...")

    organizations_data = seed_data.get("organizations", [])

    created_orgs = {}

    # Check if organizations already exist
    if not overwrite:
        existing_orgs = session.exec(select(Organization)).all()
        if existing_orgs:
            logger.info(
                f"ℹ️ Found {len(existing_orgs)} existing organizations. Use SEED_OVERWRITE=true to replace."
            )
            for org in existing_orgs:
                created_orgs[org.name] = org
            return created_orgs

    for org_data in organizations_data:
        # Generate FHIR ID
        fhir_id = f"org-{uuid.uuid4()}"

        # Create FHIR Organization resource
        fhir_org = None
        uploaded_fhir_id = None
        if settings.FHIR_ENABLED:
            try:
                fhir_org = create_org_fhir(
                    id=fhir_id,
                    name=org_data["name"],
                    type_code=org_data["type_code"],
                    address_line=org_data.get("address_line"),
                    address_city=org_data.get("address_city"),
                    address_postal_code=org_data.get("address_postal_code"),
                    address_country=org_data.get("address_country"),
                    phone=org_data.get("phone"),
                    email=org_data.get("email"),
                    ico=org_data.get("ico"),
                    dic=org_data.get("dic"),
                )
                uploaded_fhir_id = upload_fhir_resource(fhir_org)
                if uploaded_fhir_id:
                    logger.info(f"✅ Created FHIR Organization: {uploaded_fhir_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to create FHIR Organization: {e}")

        # Create database record
        org = Organization(fhir_id=uploaded_fhir_id or fhir_id, **org_data)
        session.add(org)
        session.flush()
        session.refresh(org)
        created_orgs[org_data["name"]] = org
        logger.info(f"✅ Created Organization: {org.name} (ID: {org.id})")

    session.commit()
    return created_orgs


def seed_users_and_practitioners(
    session: Session, organizations: dict, seed_data: dict, overwrite: bool = False
) -> dict:
    """Seed users, doctors, and practitioners with FHIR resources"""
    if not get_env_bool("SEED_USERS", True):
        logger.info("⏭️ Skipping users (SEED_USERS=false)")
        return {}

    logger.info("Seeding users and practitioners...")

    users_data = seed_data.get("users", [])

    # Check if users already exist
    if not overwrite:
        existing_users = session.exec(select(User)).all()
        if existing_users:
            logger.info(
                f"ℹ️ Found {len(existing_users)} existing users. Use SEED_OVERWRITE=true to replace."
            )
            created_users = {}
            for user in existing_users:
                created_users[user.email] = {"user": user}
                # Get associated doctor/practitioner
                if user.role == "doctor":
                    doctor = session.exec(
                        select(Doctor).where(Doctor.user_id == user.id)
                    ).first()
                    if doctor:
                        created_users[user.email]["doctor"] = doctor
                elif user.role == "practitioner":
                    practitioner = session.exec(
                        select(Practitioner).where(Practitioner.user_id == user.id)
                    ).first()
                    if practitioner:
                        created_users[user.email]["practitioner"] = practitioner
            return created_users

    created_users = {}

    for user_data in users_data:
        # Create user
        salt = generate_salt()
        hashed_pw = hash_password(user_data["password"], salt)
        user = User(
            email=user_data["email"],
            hashed_password=hashed_pw,
            salt=salt,
            role=user_data["role"],
            is_active=True,
        )
        session.add(user)
        session.flush()
        session.refresh(user)

        # Create FHIR Practitioner and Doctor/Practitioner records
        if user_data["role"] in ["doctor", "practitioner", "specialist"]:
            fhir_id = f"prac-{uuid.uuid4()}"
            uploaded_fhir_id = None

            if settings.FHIR_ENABLED:
                try:
                    fhir_practitioner = create_practitioner_fhir(
                        id=fhir_id,
                        name=user_data.get("practitioner_name"),
                        given_name=user_data.get("given_name"),
                        family_name=user_data.get("family_name"),
                    )
                    uploaded_fhir_id = upload_fhir_resource(fhir_practitioner)

                    # Create PractitionerRole for doctors
                    if user_data["role"] == "doctor" and uploaded_fhir_id:
                        org = organizations.get(user_data.get("organization"))
                        if org and org.fhir_id:
                            role_fhir_id = f"role-{uuid.uuid4()}"
                            fhir_role = create_role_fhir(
                                id=role_fhir_id,
                                practitioner_id=uploaded_fhir_id,
                                organization_id=org.fhir_id,
                            )
                            upload_fhir_resource(fhir_role)

                    if uploaded_fhir_id:
                        logger.info(f"✅ Created FHIR Practitioner: {uploaded_fhir_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to create FHIR Practitioner: {e}")

            if user_data["role"] == "doctor":
                org = organizations.get(user_data.get("organization"))
                doctor = Doctor(
                    fhir_id=uploaded_fhir_id or fhir_id,
                    user_id=user.id,
                    organization_id=org.id if org else None,
                    given_name=user_data.get("given_name"),
                    family_name=user_data.get("family_name"),
                )
                session.add(doctor)
                created_users[user_data["email"]] = {"user": user, "doctor": doctor}
            elif user_data["role"] in ["practitioner", "specialist"]:
                practitioner = Practitioner(
                    fhir_id=uploaded_fhir_id or fhir_id,
                    user_id=user.id,
                    identifier_ico=user_data.get("ico"),
                    given_name=user_data.get("given_name"),
                    family_name=user_data.get("family_name"),
                )
                session.add(practitioner)
                created_users[user_data["email"]] = {
                    "user": user,
                    "practitioner": practitioner,
                }
        else:
            created_users[user_data["email"]] = {"user": user}

        logger.info(f"✅ Created User: {user.email} (Role: {user.role})")

    session.commit()
    return created_users


def seed_patients(
    session: Session, organizations: dict, seed_data: dict, overwrite: bool = False
) -> list:
    """Seed patients and create FHIR Patient resources"""
    if not get_env_bool("SEED_PATIENTS", True):
        logger.info("⏭️ Skipping patients (SEED_PATIENTS=false)")
        return []

    logger.info("Seeding patients...")

    patients_data = seed_data.get("patients", [])

    # Check if patients already exist
    if not overwrite:
        existing_patients = session.exec(select(Patient)).all()
        if existing_patients:
            logger.info(
                f"ℹ️ Found {len(existing_patients)} existing patients. Use SEED_OVERWRITE=true to replace."
            )
            return existing_patients

    created_patients = []

    for patient_data in patients_data:
        fhir_id = f"pat-{uuid.uuid4()}"
        uploaded_fhir_id = None

        managing_org = None
        if patient_data.get("managing_organization"):
            managing_org = organizations.get(patient_data["managing_organization"])

        # Parse birth_date from string if needed
        birth_date_obj = None
        if patient_data.get("birth_date"):
            if isinstance(patient_data["birth_date"], str):
                birth_date_obj = date.fromisoformat(patient_data["birth_date"])
            else:
                birth_date_obj = patient_data["birth_date"]

        if settings.FHIR_ENABLED:
            try:
                fhir_patient = create_patient_fhir(
                    id=fhir_id,
                    given_name=patient_data["given_name"],
                    family_name=patient_data["family_name"],
                    identifier_rc=patient_data.get("identifier_rc"),
                    birth_date=birth_date_obj,
                    gender=patient_data.get("gender"),
                    phone=patient_data.get("phone"),
                    email=patient_data.get("email"),
                    address_text=patient_data.get("address_text"),
                    address_city=patient_data.get("address_city"),
                    address_postal_code=patient_data.get("address_postal_code"),
                    address_country=patient_data.get("address_country"),
                    insurance_company_code=patient_data.get("insurance_company_code"),
                    managing_org_id=managing_org.fhir_id if managing_org else None,
                )
                uploaded_fhir_id = upload_fhir_resource(fhir_patient)
                if uploaded_fhir_id:
                    logger.info(f"✅ Created FHIR Patient: {uploaded_fhir_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to create FHIR Patient: {e}")

        patient_dict = patient_data.copy()
        if managing_org:
            patient_dict["managing_organization_id"] = managing_org.id
        if "managing_organization" in patient_dict:
            del patient_dict["managing_organization"]
        if birth_date_obj:
            patient_dict["birth_date"] = birth_date_obj

        patient = Patient(fhir_id=uploaded_fhir_id or fhir_id, **patient_dict)
        session.add(patient)
        session.flush()
        session.refresh(patient)
        created_patients.append(patient)
        logger.info(
            f"✅ Created Patient: {patient.given_name} {patient.family_name} (ID: {patient.id})"
        )

    session.commit()
    return created_patients


def seed_mkn10_codes(session: Session) -> None:
    """Seed MKN-10 codes table"""
    logger.info("Seeding MKN-10 codes...")

    mkn10_codes = [
        ("C49.0", "Pojivová a měkká tkáň hlavy‚ obličeje a krku"),
        ("C49.1", "Pojivová a měkká tkáň horní končetiny včetně ramene"),
        ("C49.2", "Pojivová a měkká tkáň dolní končetiny včetně boku"),
        ("C49.3", "Pojivová a měkká tkáň hrudníku"),
        ("C49.4", "Pojivová a měkká tkáň břicha"),
        ("C78.0", "Sekundární maligní novotvar plic a průdušek"),
        ("C49.9", "Pojivová a měkká tkáň, blíže neurčeno"),
    ]

    for code, name in mkn10_codes:
        existing = session.exec(select(MKN10).where(MKN10.code == code)).first()
        if not existing:
            mkn10 = MKN10(code=code, name=name)
            session.add(mkn10)
            logger.info(f"✅ Created MKN-10 code: {code} - {name}")
        else:
            logger.info(f"ℹ️ MKN-10 code {code} already exists, skipping")

    session.commit()
    logger.info("✅ MKN-10 codes seeding completed")


def seed_reports(
    session: Session,
    patients: list,
    users: dict,
    organizations: dict,
    seed_data: dict,
    overwrite: bool = False,
) -> list:
    """Seed reports and create FHIR ServiceRequest resources"""
    if not get_env_bool("SEED_REPORTS", True):
        logger.info("⏭️ Skipping reports (SEED_REPORTS=false)")
        return []

    logger.info("Seeding reports...")

    # Get doctors
    doctors = [u["doctor"] for u in users.values() if "doctor" in u]

    if not doctors:
        logger.warning("⚠️ No doctors found, skipping reports")
        return []

    reports_data = seed_data.get("reports", [])

    # Check if reports already exist
    if not overwrite:
        existing_reports = session.exec(select(Report)).all()
        if existing_reports:
            logger.info(
                f"ℹ️ Found {len(existing_reports)} existing reports. Use SEED_OVERWRITE=true to replace."
            )
            return existing_reports

    created_reports = []

    for report_data in reports_data:
        patient = patients[report_data["patient_index"]]
        user_data = users.get(report_data["doctor_email"])

        if not user_data or "doctor" not in user_data:
            logger.warning(
                f"⚠️ Doctor not found for {report_data['doctor_email']}, skipping report"
            )
            continue

        doctor = user_data["doctor"]
        target_org = organizations.get(report_data["target_organization"])

        if not target_org:
            logger.warning(
                f"⚠️ Organization not found: {report_data['target_organization']}"
            )
            continue

        fhir_id = f"rep-{uuid.uuid4()}"
        uploaded_fhir_id = None

        # Parse histology_date if provided as string
        histology_date_obj = None
        if report_data.get("histology_date"):
            if isinstance(report_data["histology_date"], str):
                histology_date_obj = date.fromisoformat(report_data["histology_date"])
            else:
                histology_date_obj = report_data["histology_date"]

        if settings.FHIR_ENABLED:
            try:
                fhir_service_request = create_service_request_fhir(
                    id=fhir_id,
                    patient_id=patient.fhir_id,
                    doctor_id=doctor.fhir_id,
                    target_org_id=target_org.fhir_id,
                    status=report_data["status"].lower(),
                    created_at=datetime.now().astimezone(),
                    anamnesis=report_data.get("anamnesis"),
                    family_history=report_data.get("family_history"),
                    any_imaging_performed=report_data.get("any_imaging_performed"),
                    additional_imaging_planned=report_data.get(
                        "additional_imaging_planned"
                    ),
                    additional_imaging_note=report_data.get("additional_imaging_note"),
                    mkn10_code=report_data.get("mkn10_code"),
                    histology_performed=report_data.get("histology_performed"),
                    histology_date=histology_date_obj,
                    histology_result=report_data.get("histology_result"),
                    summary=report_data.get("summary"),
                )
                uploaded_fhir_id = upload_fhir_resource(fhir_service_request)
                if uploaded_fhir_id:
                    logger.info(f"✅ Created FHIR ServiceRequest: {uploaded_fhir_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to create FHIR ServiceRequest: {e}")

        report = Report(
            fhir_id=uploaded_fhir_id or fhir_id,
            patient_id=patient.id,
            doctor_id=doctor.id,
            target_organization_id=target_org.id,
            status=report_data["status"],
            anamnesis=report_data.get("anamnesis"),
            family_history=report_data.get("family_history"),
            any_imaging_performed=report_data.get("any_imaging_performed"),
            additional_imaging_planned=report_data.get("additional_imaging_planned"),
            additional_imaging_note=report_data.get("additional_imaging_note"),
            mkn10_code=report_data.get("mkn10_code"),
            histology_performed=report_data.get("histology_performed"),
            histology_date=histology_date_obj,
            histology_result=report_data.get("histology_result"),
            summary=report_data.get("summary"),
            created_at=datetime.now(),
        )
        session.add(report)
        session.flush()
        session.refresh(report)
        created_reports.append(report)
        logger.info(f"✅ Created Report: ID {report.id} (Status: {report.status})")

    session.commit()
    return created_reports


def main():
    """Main seeding function"""
    logger.info("=" * 80)
    logger.info("Database Seeder - PostgreSQL with FHIR Integration")
    logger.info("=" * 80)
    logger.info("")

    # Configuration from environment
    overwrite = get_env_bool("SEED_OVERWRITE", False)
    seed_orgs = get_env_bool("SEED_ORGANIZATIONS", True)
    seed_users = get_env_bool("SEED_USERS", True)
    seed_patients_flag = get_env_bool("SEED_PATIENTS", True)
    seed_reports_flag = get_env_bool("SEED_REPORTS", True)

    logger.info("Configuration:")
    logger.info(f"  SEED_ORGANIZATIONS: {seed_orgs}")
    logger.info(f"  SEED_USERS: {seed_users}")
    logger.info(f"  SEED_PATIENTS: {seed_patients_flag}")
    logger.info(f"  SEED_REPORTS: {seed_reports_flag}")
    logger.info(f"  SEED_OVERWRITE: {overwrite}")
    logger.info(f"  FHIR_ENABLED: {settings.FHIR_ENABLED}")
    logger.info("")

    # Load seed data
    seed_data = get_seed_data()

    # Create database engine
    engine = create_database_engine()

    # Create tables
    create_tables(engine)

    # Create session
    with Session(engine) as session:
        try:
            organizations = {}
            users = {}
            patients = []
            reports = []

            # Seed organizations
            if seed_orgs:
                organizations = seed_organizations(session, seed_data, overwrite)
                logger.info("")
            else:
                # Load existing organizations for reference
                existing_orgs = session.exec(select(Organization)).all()
                organizations = {org.name: org for org in existing_orgs}

            # Seed users and practitioners
            if seed_users:
                users = seed_users_and_practitioners(
                    session, organizations, seed_data, overwrite
                )
                logger.info("")
            else:
                # Load existing users for reference
                existing_users = session.exec(select(User)).all()
                for user in existing_users:
                    user_dict = {"user": user}
                    if user.role == "doctor":
                        doctor = session.exec(
                            select(Doctor).where(Doctor.user_id == user.id)
                        ).first()
                        if doctor:
                            user_dict["doctor"] = doctor
                    elif user.role == "practitioner":
                        practitioner = session.exec(
                            select(Practitioner).where(Practitioner.user_id == user.id)
                        ).first()
                        if practitioner:
                            user_dict["practitioner"] = practitioner
                    users[user.email] = user_dict

            # Seed patients
            if seed_patients_flag:
                patients = seed_patients(session, organizations, seed_data, overwrite)
                logger.info("")
            else:
                # Load existing patients for reference
                patients = session.exec(select(Patient)).all()

            # Seed MKN-10 codes (required for reports)
            seed_mkn10_codes(session)
            logger.info("")

            # Seed reports
            if seed_reports_flag:
                reports = seed_reports(
                    session, patients, users, organizations, seed_data, overwrite
                )
                logger.info("")
            else:
                # Load existing reports for summary
                reports = session.exec(select(Report)).all()

            logger.info("=" * 80)
            logger.info("✅ Database seeding completed successfully!")
            logger.info("=" * 80)
            logger.info(f"   Organizations: {len(organizations)}")
            logger.info(f"   Users: {len(users)}")
            logger.info(f"   Patients: {len(patients)}")
            logger.info(f"   Reports: {len(reports)}")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"❌ Error during seeding: {e}", exc_info=True)
            session.rollback()
            raise


if __name__ == "__main__":
    main()
