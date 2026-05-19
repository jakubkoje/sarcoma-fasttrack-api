"""
IRIS Vector Search Example with FHIR Data

This demonstrates how to:
1. Extract text from FHIR resources
2. Generate embeddings using sentence-transformers
3. Store embeddings in IRIS
4. Perform vector similarity search
"""

import requests
from sentence_transformers import SentenceTransformer
import intersystems_iris.dbapi._DBAPI as iris
import numpy as np

# FHIR Server Settings
FHIR_URL = "http://localhost:32783/csp/healthshare/demo/fhir/r4"
AUTH = ("_SYSTEM", "ISCDEMO")

# IRIS Connection Settings
IRIS_HOST = "localhost"
IRIS_PORT = 32782
IRIS_NAMESPACE = "DEMO"
IRIS_USERNAME = "_SYSTEM"
IRIS_PASSWORD = "ISCDEMO"

def get_fhir_resource(resource_type, resource_id):
    """Retrieve a FHIR resource"""
    url = f"{FHIR_URL}/{resource_type}/{resource_id}"
    response = requests.get(url, auth=AUTH)
    return response.json() if response.status_code == 200 else None

def extract_text_from_observation(observation):
    """Extract meaningful text from an Observation resource"""
    text_parts = []
    
    # Code/description
    if 'code' in observation and 'coding' in observation['code']:
        for coding in observation['code']['coding']:
            if 'display' in coding:
                text_parts.append(coding['display'])
    
    # Value
    if 'valueString' in observation:
        text_parts.append(observation['valueString'])
    elif 'valueQuantity' in observation:
        value = observation['valueQuantity']
        text_parts.append(f"{value.get('value', '')} {value.get('unit', '')}")
    
    return " - ".join(text_parts)

def extract_text_from_service_request(service_request):
    """Extract text from ServiceRequest"""
    text_parts = []
    
    if 'code' in service_request and 'text' in service_request['code']:
        text_parts.append(service_request['code']['text'])
    
    if 'note' in service_request:
        for note in service_request['note']:
            if 'text' in note:
                text_parts.append(note['text'])
    
    return " - ".join(text_parts)

def create_vector_table(connection):
    """Create a table in IRIS to store vectors"""
    cursor = connection.cursor()
    
    # Drop table if exists
    try:
        cursor.execute("DROP TABLE ClinicalNotes")
    except:
        pass
    
    # Create table with vector column
    # VECTOR(DECIMAL, 384) means 384-dimensional vector with decimal values
    # 384 is the dimension for 'all-MiniLM-L6-v2' model
    cursor.execute("""
        CREATE TABLE ClinicalNotes (
            id INTEGER PRIMARY KEY,
            fhir_resource_type VARCHAR(50),
            fhir_resource_id VARCHAR(50),
            patient_id VARCHAR(50),
            text_content VARCHAR(5000),
            embedding VECTOR(DECIMAL, 384)
        )
    """)
    
    print("✅ Created ClinicalNotes table with vector column")
    connection.commit()

def store_embeddings(connection, model):
    """Fetch FHIR data, generate embeddings, and store in IRIS"""
    cursor = connection.cursor()
    
    # Get all observations for patient pat-1
    observations_url = f"{FHIR_URL}/Observation?patient=Patient/pat-1"
    response = requests.get(observations_url, auth=AUTH)
    
    if response.status_code == 200:
        bundle = response.json()
        
        for idx, entry in enumerate(bundle.get('entry', [])):
            resource = entry['resource']
            text = extract_text_from_observation(resource)
            
            # Generate embedding
            embedding = model.encode(text)
            
            # Convert to list for SQL insertion
            embedding_list = embedding.tolist()
            embedding_str = f"TO_VECTOR('[{','.join(map(str, embedding_list))}]')"
            
            # Insert into IRIS
            cursor.execute(f"""
                INSERT INTO ClinicalNotes 
                (id, fhir_resource_type, fhir_resource_id, patient_id, text_content, embedding)
                VALUES (?, ?, ?, ?, ?, {embedding_str})
            """, (idx + 1, 'Observation', resource['id'], 'pat-1', text))
            
            print(f"✅ Stored: {text[:50]}...")
    
    # Get ServiceRequests
    sr_url = f"{FHIR_URL}/ServiceRequest?patient=Patient/pat-1"
    response = requests.get(sr_url, auth=AUTH)
    
    if response.status_code == 200:
        bundle = response.json()
        offset = 100  # Start IDs at 100 to avoid conflicts
        
        for idx, entry in enumerate(bundle.get('entry', [])):
            resource = entry['resource']
            text = extract_text_from_service_request(resource)
            
            if text:  # Only store if there's text
                embedding = model.encode(text)
                embedding_list = embedding.tolist()
                embedding_str = f"TO_VECTOR('[{','.join(map(str, embedding_list))}]')"
                
                cursor.execute(f"""
                    INSERT INTO ClinicalNotes 
                    (id, fhir_resource_type, fhir_resource_id, patient_id, text_content, embedding)
                    VALUES (?, ?, ?, ?, ?, {embedding_str})
                """, (offset + idx, 'ServiceRequest', resource['id'], 'pat-1', text))
                
                print(f"✅ Stored: {text[:50]}...")
    
    connection.commit()

def vector_search(connection, model, query_text, top_k=3):
    """Perform vector similarity search"""
    cursor = connection.cursor()
    
    # Generate embedding for query
    query_embedding = model.encode(query_text)
    query_embedding_list = query_embedding.tolist()
    query_vector_str = f"TO_VECTOR('[{','.join(map(str, query_embedding_list))}]')"
    
    # Perform vector search using VECTOR_DOT_PRODUCT
    # Higher dot product = more similar
    cursor.execute(f"""
        SELECT TOP {top_k}
            id,
            fhir_resource_type,
            fhir_resource_id,
            text_content,
            VECTOR_DOT_PRODUCT(embedding, {query_vector_str}) as similarity
        FROM ClinicalNotes
        ORDER BY similarity DESC
    """)
    
    results = cursor.fetchall()
    
    print(f"\n🔍 Search results for: '{query_text}'")
    print("=" * 80)
    
    for row in results:
        print(f"\nSimilarity: {row[4]:.4f}")
        print(f"Resource: {row[1]}/{row[2]}")
        print(f"Text: {row[3]}")
        print("-" * 80)
    
    return results

def main():
    print("IRIS Vector Search Demo\n")
    
    # 1. Load embedding model
    print("📥 Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ Model loaded\n")
    
    # 2. Connect to IRIS
    print("🔌 Connecting to IRIS...")
    connection = iris.connect(
        hostname=IRIS_HOST,
        port=IRIS_PORT,
        namespace=IRIS_NAMESPACE,
        username=IRIS_USERNAME,
        password=IRIS_PASSWORD
    )
    print("✅ Connected to IRIS\n")
    
    # 3. Create vector table
    print("📊 Creating vector table...")
    create_vector_table(connection)
    print()
    
    # 4. Store embeddings
    print("💾 Fetching FHIR data and storing embeddings...")
    store_embeddings(connection, model)
    print()
    
    # 5. Perform searches
    print("\n" + "=" * 80)
    print("VECTOR SEARCH EXAMPLES")
    print("=" * 80)
    
    # Example searches
    vector_search(connection, model, "tumor pathology results")
    vector_search(connection, model, "patient complaints and symptoms")
    vector_search(connection, model, "planned medical procedures")
    
    connection.close()
    print("\n✅ Demo complete!")

if __name__ == "__main__":
    main()
