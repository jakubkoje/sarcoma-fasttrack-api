-- IRIS Vector Search Tables for Report Classification
-- Execute these in IRIS SQL to create the necessary tables

-- Table for storing report embeddings
CREATE TABLE ReportEmbeddings (
    id INTEGER PRIMARY KEY,
    report_id INTEGER NOT NULL,
    fhir_service_request_id VARCHAR(100),
    report_text LONGVARCHAR,
    embedding VECTOR(DECIMAL, 384),
    specialist_classification VARCHAR(50),
    severity_classification VARCHAR(20),
    classification_confidence DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for specialist classification examples (training data)
CREATE TABLE SpecialistExamples (
    id INTEGER PRIMARY KEY,
    specialist_type VARCHAR(50) NOT NULL,  -- 'surgeon' or 'oncologist'
    example_text LONGVARCHAR NOT NULL,
    embedding VECTOR(DECIMAL, 384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for severity classification examples (training data)
CREATE TABLE SeverityExamples (
    id INTEGER PRIMARY KEY,
    severity_level VARCHAR(20) NOT NULL,  -- 'critical', 'medium', 'low'
    severity_code INTEGER NOT NULL,  -- 1=critical, 2=medium, 3=low
    example_text LONGVARCHAR NOT NULL,
    embedding VECTOR(DECIMAL, 384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for faster lookups
CREATE INDEX idx_report_embeddings_report_id ON ReportEmbeddings(report_id);
CREATE INDEX idx_specialist_examples_type ON SpecialistExamples(specialist_type);
CREATE INDEX idx_severity_examples_level ON SeverityExamples(severity_level);
