# Classification Endpoints - Quick Reference

## Available Endpoints

### 1. Create Report (Auto-Classification)
```
POST /api/v1/reports
```
Automatically classifies the report and returns classification in response.

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/reports" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "patient_id": 1,
    "doctor_id": 1,
    "target_organization_id": 1,
    "anamnesis": "Large tumor requiring surgical resection",
    "histology_result": "Confirmed sarcoma",
    "summary": "Urgent surgical intervention needed"
  }'
```

**Response includes**:
```json
{
  "id": 1,
  "specialist": "surgeon",
  "specialist_confidence": 0.87,
  "severity": "critical",
  "severity_code": 1,
  "severity_confidence": 0.92,
  "overall_confidence": 0.895
}
```

---

### 2. Get Classification
```
GET /api/v1/reports/{report_id}/classification
```
Retrieve stored classification for a report.

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/reports/1/classification" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response**:
```json
{
  "specialist": "surgeon",
  "severity": "critical",
  "confidence": 0.895
}
```

---

### 3. Reclassify Report
```
POST /api/v1/reports/{report_id}/reclassify
```
Manually trigger reclassification.

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/reports/1/reclassify" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response**:
```json
{
  "specialist": "oncologist",
  "specialist_confidence": 0.85,
  "severity": "medium",
  "severity_code": 2,
  "severity_confidence": 0.79,
  "overall_confidence": 0.82
}
```

---

## Classification Values

### Specialists
- `surgeon` - Surgical intervention needed
- `oncologist` - Medical oncology/systemic therapy

### Severity Levels
- `critical` (code: 1) - Urgent/emergency cases
- `medium` (code: 2) - Standard priority
- `low` (code: 3) - Routine follow-up

---

## Setup Required

Before testing, run:

1. **Create IRIS tables**:
   ```bash
   # Execute SQL in IRIS
   cat scripts/iris_vector_schema.sql
   ```

2. **Load training data**:
   ```bash
   python scripts/init_classification_examples.py
   ```

---

## Test Cases

### Surgical + Critical
```json
{
  "anamnesis": "Large tumor requiring urgent surgical excision",
  "histology_result": "Confirmed liposarcoma",
  "summary": "Immediate surgical intervention needed"
}
```

### Oncologist + Medium
```json
{
  "anamnesis": "Patient on chemotherapy for metastatic disease",
  "histology_result": "Stable on current regimen",
  "summary": "Continue systemic therapy protocol"
}
```

### Oncologist + Low
```json
{
  "anamnesis": "Routine follow-up after complete resection",
  "histology_result": "No evidence of recurrence",
  "summary": "Surveillance imaging negative for 3 years"
}
```

---

## Full Documentation

See [`TESTING_CLASSIFICATION.md`](file:///Users/patrikkozlik/Projects/hackatons/brno/SarcomFasttrack-BE/TESTING_CLASSIFICATION.md) for comprehensive testing guide.
