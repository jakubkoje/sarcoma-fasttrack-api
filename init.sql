-- Imaging modality enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'imaging_modality') THEN
        CREATE TYPE imaging_modality AS ENUM ('US', 'MRI', 'CT', 'PET_CT', 'PET_MRI');
    END IF;
END $$;

-- Organizations table
CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    fhir_id VARCHAR UNIQUE,
    name VARCHAR,
    type_code VARCHAR,
    ico VARCHAR,
    dic VARCHAR,
    phone VARCHAR,
    email VARCHAR,
    address_line VARCHAR,
    address_city VARCHAR,
    address_postal_code VARCHAR,
    address_country VARCHAR
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR NOT NULL UNIQUE,
    hashed_password VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    role VARCHAR DEFAULT 'coordinator',
    salt VARCHAR NOT NULL
);

-- Practitioners table
CREATE TABLE IF NOT EXISTS practitioners (
    id SERIAL PRIMARY KEY,
    fhir_id VARCHAR UNIQUE,
    user_id INTEGER UNIQUE REFERENCES users(id),
    identifier_ico VARCHAR,
    family_name VARCHAR,
    given_name VARCHAR,
    phone VARCHAR,
    email VARCHAR,
    address_line VARCHAR,
    address_city VARCHAR,
    address_postal_code VARCHAR,
    address_country VARCHAR
);

-- Doctors table
CREATE TABLE IF NOT EXISTS doctors (
    id SERIAL PRIMARY KEY,
    fhir_id VARCHAR UNIQUE,
    user_id INTEGER UNIQUE REFERENCES users(id),
    organization_id INTEGER REFERENCES organizations(id),
    family_name VARCHAR,
    given_name VARCHAR,
    phone VARCHAR,
    email VARCHAR,
    specialty_code VARCHAR,
    role_code VARCHAR
);

-- Patients table
CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    fhir_id VARCHAR UNIQUE,
    identifier_rc VARCHAR,
    insurance_company_code VARCHAR,
    family_name VARCHAR,
    given_name VARCHAR,
    phone VARCHAR,
    email VARCHAR,
    address_text VARCHAR,
    address_city VARCHAR,
    address_postal_code VARCHAR,
    address_country VARCHAR,
    birth_date DATE,
    gender VARCHAR,
    managing_organization_id INTEGER REFERENCES organizations(id)
);

-- MKN-10 codes table (must be created before reports due to foreign key)
CREATE TABLE IF NOT EXISTS mkn10_code (
    code VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL
);

-- Reports table
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    fhir_id VARCHAR UNIQUE,
    patient_id INTEGER REFERENCES patients(id),
    doctor_id INTEGER REFERENCES doctors(id),
    target_organization_id INTEGER REFERENCES organizations(id),
    status VARCHAR DEFAULT 'DRAFT',
    is_new_patient BOOLEAN,
    any_imaging_performed BOOLEAN,
    additional_imaging_planned BOOLEAN,
    additional_imaging_note TEXT,
    anamnesis TEXT,
    family_history TEXT,
    anticoagulant_medication BOOLEAN,
    anticoagulant_detail TEXT,
    histology_performed BOOLEAN,
    histology_date DATE,
    histology_result TEXT,
    summary TEXT,
    mkn10_code VARCHAR REFERENCES mkn10_code(code),
    feedback_specialist TEXT,
    attachment_path VARCHAR,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Imaging examinations table
CREATE TABLE IF NOT EXISTS imaging_examinations (
    id SERIAL PRIMARY KEY,
    report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    modality imaging_modality,
    exam_date DATE,
    description TEXT
);

-- Function to update reports.updated_at timestamp
CREATE OR REPLACE FUNCTION set_reports_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at on reports
DROP TRIGGER IF EXISTS trg_reports_set_updated_at ON reports;
CREATE TRIGGER trg_reports_set_updated_at
BEFORE UPDATE ON reports
FOR EACH ROW
EXECUTE FUNCTION set_reports_updated_at();

-- Seed initial MKN-10 codes
INSERT INTO mkn10_code (code, name) VALUES
    ('C49.0', 'Pojivová a měkká tkáň hlavy‚ obličeje a krku'),
    ('C49.1', 'Pojivová a měkká tkáň horní končetiny včetně ramene'),
    ('C49.2', 'Pojivová a měkká tkáň dolní končetiny včetně boku'),
    ('C49.3', 'Pojivová a měkká tkáň hrudníku'),
    ('C49.4', 'Pojivová a měkká tkáň břicha')
ON CONFLICT (code) DO NOTHING;
