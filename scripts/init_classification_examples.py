"""
Initialize Classification Training Examples in IRIS
Creates synthetic training data for specialist and severity classification
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.embedding_service import generate_embedding
from app.services.vector_search_service import execute_iris_sql
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Training examples for SPECIALIST classification
SPECIALIST_EXAMPLES = {
    "surgeon": [
        "Large soft tissue mass in thigh requiring surgical excision and biopsy",
        "Tumor resection recommended for liposarcoma in retroperitoneum",
        "Surgical intervention needed for rapidly growing sarcoma in arm",
        "Patient requires wide local excision of myxofibrosarcoma",
        "Operative treatment planned for dedifferentiated liposarcoma",
        "Surgical debulking necessary for large abdominal sarcoma",
        "Limb-sparing surgery recommended for osteosarcoma",
        "Amputation consideration for advanced extremity sarcoma",
        "Surgical margins assessment needed post-resection",
        "Re-excision required due to positive surgical margins",
    ],
    "oncologist": [
        "Chemotherapy regimen recommended for metastatic sarcoma",
        "Radiation therapy planning for unresectable tumor",
        "Systemic treatment with doxorubicin and ifosfamide indicated",
        "Immunotherapy trial enrollment considered for advanced case",
        "Palliative care consultation for stage IV sarcoma",
        "Adjuvant chemotherapy following surgical resection",
        "Targeted therapy with pazopanib for soft tissue sarcoma",
        "Clinical trial participation for refractory sarcoma",
        "Neoadjuvant chemotherapy to shrink tumor before surgery",
        "Radiation oncology referral for local control",
        "Metastatic disease to lungs requiring systemic therapy",
        "Progression on first-line chemotherapy, second-line options needed",
    ],
}

# Training examples for SEVERITY classification
SEVERITY_EXAMPLES = {
    "critical": [  # Code 1
        "Rapidly growing tumor with severe pain and functional impairment",
        "Emergency presentation with tumor rupture and hemorrhage",
        "Metastatic disease with multiple organ involvement",
        "Acute compartment syndrome from expanding sarcoma",
        "Pathological fracture through tumor site requiring immediate intervention",
        "Spinal cord compression from paraspinal sarcoma",
        "Vascular compromise from tumor compression",
        "Sepsis secondary to infected necrotic tumor",
        "Respiratory distress from mediastinal mass",
        "Critical limb ischemia from tumor invasion",
    ],
    "medium": [  # Code 2
        "Stable soft tissue mass with gradual growth over months",
        "Incidental finding of small retroperitoneal mass on imaging",
        "Follow-up imaging showing minimal interval change",
        "Post-operative surveillance with no evidence of recurrence",
        "Asymptomatic patient with imaging findings requiring evaluation",
        "Routine screening detected abnormality",
        "Mild symptoms with well-differentiated tumor histology",
        "Localized disease with good performance status",
        "Planned elective surgical resection",
        "Stable disease on current treatment regimen",
    ],
    "low": [  # Code 3
        "Benign-appearing lipoma requiring confirmation",
        "Small superficial mass with no concerning features",
        "Routine follow-up after complete resection",
        "Surveillance imaging showing no recurrence for 5 years",
        "Asymptomatic patient with low-grade histology",
        "Completely resected tumor with negative margins",
        "Slow-growing mass with benign characteristics",
        "Post-treatment surveillance with excellent response",
        "Minor symptoms well-controlled with conservative management",
        "Low-risk tumor with favorable prognosis",
    ],
}


def init_specialist_examples():
    """Initialize specialist classification examples"""
    logger.info("Initializing specialist classification examples...")
    
    example_id = 1
    for specialist_type, examples in SPECIALIST_EXAMPLES.items():
        logger.info(f"Processing {specialist_type} examples...")
        
        for example_text in examples:
            # Generate embedding
            embedding = generate_embedding(example_text)
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
            
            # Escape quotes
            safe_text = example_text.replace("'", "''")
            
            # Insert into IRIS
            sql = f"""
            INSERT INTO SpecialistExamples 
            (id, specialist_type, example_text, embedding)
            VALUES (
                {example_id},
                '{specialist_type}',
                '{safe_text}',
                TO_VECTOR('{embedding_str}')
            )
            """
            
            result = execute_iris_sql(sql)
            if result:
                logger.info(f"  ✅ Inserted example {example_id}: {example_text[:50]}...")
            else:
                logger.error(f"  ❌ Failed to insert example {example_id}")
            
            example_id += 1
    
    logger.info(f"✅ Specialist examples initialized ({example_id - 1} total)")


def init_severity_examples():
    """Initialize severity classification examples"""
    logger.info("Initializing severity classification examples...")
    
    severity_codes = {
        "critical": 1,
        "medium": 2,
        "low": 3
    }
    
    example_id = 1
    for severity_level, examples in SEVERITY_EXAMPLES.items():
        severity_code = severity_codes[severity_level]
        logger.info(f"Processing {severity_level} (code {severity_code}) examples...")
        
        for example_text in examples:
            # Generate embedding
            embedding = generate_embedding(example_text)
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
            
            # Escape quotes
            safe_text = example_text.replace("'", "''")
            
            # Insert into IRIS
            sql = f"""
            INSERT INTO SeverityExamples 
            (id, severity_level, severity_code, example_text, embedding)
            VALUES (
                {example_id},
                '{severity_level}',
                {severity_code},
                '{safe_text}',
                TO_VECTOR('{embedding_str}')
            )
            """
            
            result = execute_iris_sql(sql)
            if result:
                logger.info(f"  ✅ Inserted example {example_id}: {example_text[:50]}...")
            else:
                logger.error(f"  ❌ Failed to insert example {example_id}")
            
            example_id += 1
    
    logger.info(f"✅ Severity examples initialized ({example_id - 1} total)")


def main():
    """Main initialization function"""
    print("=" * 80)
    print("IRIS Classification Training Data Initialization")
    print("=" * 80)
    print()
    
    print("This script will populate the IRIS database with training examples for:")
    print("  - Specialist classification (surgeon, oncologist)")
    print("  - Severity classification (critical=1, medium=2, low=3)")
    print()
    
    # Initialize specialist examples
    init_specialist_examples()
    print()
    
    # Initialize severity examples
    init_severity_examples()
    print()
    
    print("=" * 80)
    print("✅ Initialization complete!")
    print("=" * 80)
    print()
    print("You can now use the classification service to classify reports.")
    print("The system will use vector similarity search to match reports")
    print("against these training examples.")


if __name__ == "__main__":
    main()
