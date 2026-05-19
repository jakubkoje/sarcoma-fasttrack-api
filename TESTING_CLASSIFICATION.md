# Testing Vector Search Classification Endpoints

This guide shows how to test the vector search classification system.

## Prerequisites

1. **Setup IRIS tables**:
   ```bash
   # Execute the SQL in IRIS SQL interface
   cat scripts/iris_vector_schema.sql
   ```

2. **Load training data**:
   ```bash
   python scripts/init_classification_examples.py
   ```

3. **Get authentication token**:
   ```bash
   # Login to get token
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "your-email@example.com",
       "password": "your-password"
     }'
   
   # Save the token from response
   export TOKEN="your-access-token-here"
   ```

## Test Endpoints

### 1. Create Report with Automatic Classification

**Endpoint**: `POST /api/v1/reports`

This automatically classifies the report on creation.

#### Test Case 1: Surgical Case (Expected: surgeon + critical)

```bash
curl -X POST "http://localhost:8000/api/v1/reports" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "patient_id": 1,
    "doctor_id": 1,
    "target_organization_id": 1,
    "status": "ACTIVE",
    "anamnesis": "Patient presents with large soft tissue mass in thigh requiring urgent evaluation",
    "histology_result": "Biopsy confirms liposarcoma, surgical resection recommended",
    "summary": "Large tumor requiring immediate surgical intervention and wide local excision"
  }'
```

**Expected Response**:
```json
{
  "id": 1,
  "fhir_id": "rep-...",
  "patient_id": 1,
  "doctor_id": 1,
  "target_organization_id": 1,
  "status": "ACTIVE",
  "specialist": "surgeon",
  "specialist_confidence": 0.87,
  "severity": "critical",
  "severity_code": 1,
  "severity_confidence": 0.92,
  "overall_confidence": 0.895
}
```

#### Test Case 2: Oncology Case (Expected: oncologist + medium)

```bash
curl -X POST "http://localhost:8000/api/v1/reports" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "patient_id": 1,
    "doctor_id": 1,
    "target_organization_id": 1,
    "status": "ACTIVE",
    "anamnesis": "Patient on chemotherapy regimen for metastatic sarcoma",
    "histology_result": "Previously confirmed sarcoma, currently on systemic therapy",
    "summary": "Stable disease on imaging, continuing current treatment protocol"
  }'
```

**Expected Response**:
```json
{
  "id": 2,
  "specialist": "oncologist",
  "specialist_confidence": 0.85,
  "severity": "medium",
  "severity_code": 2,
  "severity_confidence": 0.79,
  "overall_confidence": 0.82
}
```

#### Test Case 3: Low Priority Case (Expected: oncologist + low)

```bash
curl -X POST "http://localhost:8000/api/v1/reports" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "patient_id": 1,
    "doctor_id": 1,
    "target_organization_id": 1,
    "status": "DRAFT",
    "anamnesis": "Routine follow-up after complete resection",
    "histology_result": "Previously resected low-grade tumor with negative margins",
    "summary": "Surveillance imaging shows no evidence of recurrence for 3 years"
  }'
```

**Expected Response**:
```json
{
  "id": 3,
  "specialist": "oncologist",
  "specialist_confidence": 0.72,
  "severity": "low",
  "severity_code": 3,
  "severity_confidence": 0.88,
  "overall_confidence": 0.80
}
```

### 2. Get Classification for Existing Report

**Endpoint**: `GET /api/v1/reports/{report_id}/classification`

Retrieves stored classification results from IRIS.

```bash
curl -X GET "http://localhost:8000/api/v1/reports/1/classification" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response**:
```json
{
  "specialist": "surgeon",
  "severity": "critical",
  "confidence": 0.895
}
```

**Error Case** (no classification found):
```json
{
  "detail": "No classification found for this report. Try reclassifying."
}
```

### 3. Reclassify Report

**Endpoint**: `POST /api/v1/reports/{report_id}/reclassify`

Manually triggers reclassification (useful after updating report or training data).

```bash
curl -X POST "http://localhost:8000/api/v1/reports/1/reclassify" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response**:
```json
{
  "specialist": "surgeon",
  "specialist_confidence": 0.87,
  "severity": "critical",
  "severity_code": 1,
  "severity_confidence": 0.92,
  "overall_confidence": 0.895
}
```

### 4. List All Reports (with classifications)

**Endpoint**: `GET /api/v1/reports`

```bash
curl -X GET "http://localhost:8000/api/v1/reports" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response**:
```json
[
  {
    "id": 1,
    "specialist": "surgeon",
    "severity": "critical",
    "severity_code": 1,
    ...
  },
  {
    "id": 2,
    "specialist": "oncologist",
    "severity": "medium",
    "severity_code": 2,
    ...
  }
]
```

### 5. Get Single Report (with classification)

**Endpoint**: `GET /api/v1/reports/{report_id}`

```bash
curl -X GET "http://localhost:8000/api/v1/reports/1" \
  -H "Authorization: Bearer $TOKEN"
```

## Verification Checklist

### ✅ Step 1: Verify IRIS Tables Created
```sql
-- Run in IRIS SQL interface
SELECT COUNT(*) FROM SpecialistExamples;  -- Should return 22
SELECT COUNT(*) FROM SeverityExamples;     -- Should return 30
SELECT COUNT(*) FROM ReportEmbeddings;     -- Should return 0 initially
```

### ✅ Step 2: Verify Training Data Loaded
```bash
python scripts/init_classification_examples.py
```

Expected output:
```
✅ Specialist examples initialized (22 total)
✅ Severity examples initialized (30 total)
```

### ✅ Step 3: Create Test Report
Use Test Case 1 above (surgical case).

### ✅ Step 4: Verify Classification Stored in IRIS
```sql
-- Run in IRIS SQL interface
SELECT 
    report_id,
    specialist_classification,
    severity_classification,
    classification_confidence
FROM ReportEmbeddings
WHERE report_id = 1;
```

Expected result:
```
report_id | specialist_classification | severity_classification | classification_confidence
----------|---------------------------|-------------------------|-------------------------
1         | surgeon                   | critical                | 0.895
```

### ✅ Step 5: Test Classification Endpoint
```bash
curl -X GET "http://localhost:8000/api/v1/reports/1/classification" \
  -H "Authorization: Bearer $TOKEN"
```

### ✅ Step 6: Test Reclassification
```bash
curl -X POST "http://localhost:8000/api/v1/reports/1/reclassify" \
  -H "Authorization: Bearer $TOKEN"
```

## Troubleshooting

### Issue: "No classification found"
**Solution**: The report was created before the classification system was set up. Use the reclassify endpoint:
```bash
curl -X POST "http://localhost:8000/api/v1/reports/{id}/reclassify" \
  -H "Authorization: Bearer $TOKEN"
```

### Issue: Classification confidence is low (<0.5)
**Solution**: Add more relevant training examples to `scripts/init_classification_examples.py` and re-run initialization.

### Issue: IRIS connection errors
**Solution**: 
1. Verify IRIS is running: `curl http://localhost:32783`
2. Check `IRIS_SQL_URL` in config
3. Verify credentials in `.env`

### Issue: Wrong specialist classification
**Solution**: Review training examples in `scripts/init_classification_examples.py`. Add more examples that match your use case.

## Testing with Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your-token-here"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Create report
report_data = {
    "patient_id": 1,
    "doctor_id": 1,
    "target_organization_id": 1,
    "anamnesis": "Large tumor requiring surgical resection",
    "histology_result": "Confirmed liposarcoma",
    "summary": "Urgent surgical intervention needed"
}

response = requests.post(
    f"{BASE_URL}/reports",
    json=report_data,
    headers=headers
)
report = response.json()
print(f"Created report {report['id']}")
print(f"Specialist: {report['specialist']} ({report['specialist_confidence']:.2f})")
print(f"Severity: {report['severity']} ({report['severity_confidence']:.2f})")

# Get classification
response = requests.get(
    f"{BASE_URL}/reports/{report['id']}/classification",
    headers=headers
)
classification = response.json()
print(f"Classification: {classification}")

# Reclassify
response = requests.post(
    f"{BASE_URL}/reports/{report['id']}/reclassify",
    headers=headers
)
new_classification = response.json()
print(f"Reclassified: {new_classification}")
```

## Expected Classification Results

| Report Content | Expected Specialist | Expected Severity |
|----------------|---------------------|-------------------|
| "Surgical resection needed" | surgeon | critical/medium |
| "Chemotherapy regimen" | oncologist | medium |
| "Radiation therapy" | oncologist | medium |
| "Emergency tumor rupture" | surgeon | critical |
| "Routine follow-up" | oncologist | low |
| "Post-operative surveillance" | oncologist | low |
| "Metastatic disease" | oncologist | critical/medium |
| "Limb-sparing surgery" | surgeon | critical/medium |

## API Documentation

Once the server is running, view the interactive API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Look for the `/reports` endpoints with classification fields in the response schemas.
