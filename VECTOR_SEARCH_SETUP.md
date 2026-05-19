# Vector Search Classification Setup

This document explains how to set up and use the vector search-based report classification system.

## Overview

The system automatically classifies medical reports when they are created using:
- **Specialist Classification**: Determines if a surgeon or oncologist should review
- **Severity Classification**: Assigns critical (1), medium (2), or low (3) priority

## Setup Steps

### 1. Create IRIS Tables

Execute the SQL schema in IRIS:

```bash
# From the project root
cat scripts/iris_vector_schema.sql
```

Copy and execute the SQL in IRIS SQL interface or via REST API.

### 2. Initialize Training Data

Run the initialization script to populate training examples:

```bash
python scripts/init_classification_examples.py
```

This will:
- Create 22 specialist examples (10 surgeon, 12 oncologist)
- Create 30 severity examples (10 critical, 10 medium, 10 low)
- Generate embeddings for all examples
- Store them in IRIS

### 3. Verify Setup

Check that tables are populated:

```sql
SELECT COUNT(*) FROM SpecialistExamples;  -- Should return 22
SELECT COUNT(*) FROM SeverityExamples;     -- Should return 30
```

## Usage

### Automatic Classification

When a report is created via POST `/api/v1/reports`, it will automatically:
1. Extract text from report fields
2. Generate embedding
3. Classify specialist and severity
4. Store results in IRIS

### Manual Classification

Get classification for an existing report:

```bash
GET /api/v1/reports/{report_id}/classification
```

Response:
```json
{
  "specialist": "oncologist",
  "specialist_confidence": 0.85,
  "severity": "critical",
  "severity_code": 1,
  "severity_confidence": 0.92,
  "overall_confidence": 0.88
}
```

### Reclassify a Report

Trigger reclassification:

```bash
POST /api/v1/reports/{report_id}/reclassify
```

## How It Works

### Vector Similarity Search

1. Report text is converted to a 384-dimensional embedding using `all-MiniLM-L6-v2`
2. IRIS performs vector similarity search (dot product) against training examples
3. Top 5 most similar examples are retrieved
4. Votes are weighted by similarity scores
5. Winner is selected based on highest weighted vote

### Example

Report: "Large tumor requiring surgical resection"

Vector search finds:
1. "Tumor resection recommended..." (surgeon, similarity: 0.92)
2. "Surgical intervention needed..." (surgeon, similarity: 0.88)
3. "Wide local excision..." (surgeon, similarity: 0.85)
4. "Chemotherapy regimen..." (oncologist, similarity: 0.45)
5. "Radiation therapy..." (oncologist, similarity: 0.42)

Result: **surgeon** (confidence: 0.87)

## Configuration

IRIS settings in `.env`:

```
IRIS_HOST=host.docker.internal
IRIS_PORT=32783
IRIS_NAMESPACE=DEMO
IRIS_USERNAME=_SYSTEM
IRIS_PASSWORD=ISCDEMO
```

## Adding More Training Examples

To improve classification accuracy, add more examples to `scripts/init_classification_examples.py`:

```python
SPECIALIST_EXAMPLES = {
    "surgeon": [
        "Your new surgical example here",
        # ... more examples
    ],
    "oncologist": [
        "Your new oncology example here",
        # ... more examples
    ]
}
```

Then re-run the initialization script.

## Troubleshooting

### No classification results
- Check IRIS is running and accessible
- Verify tables are created
- Ensure training data is loaded

### Low confidence scores
- Add more diverse training examples
- Check report text extraction is working
- Verify embeddings are being generated

### IRIS connection errors
- Check `IRIS_SQL_URL` in config
- Verify credentials
- Test IRIS REST API manually
