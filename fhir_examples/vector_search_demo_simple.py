"""
IRIS Vector Search Example with FHIR Data (Using REST API)

This demonstrates how to:
1. Extract text from FHIR resources
2. Generate embeddings using sentence-transformers
3. Store embeddings in IRIS via SQL REST API
4. Perform vector similarity search

Note: This uses IRIS SQL REST API instead of native driver
"""

import requests
from sentence_transformers import SentenceTransformer
import json

# FHIR Server Settings
FHIR_URL = "http://localhost:32783/csp/healthshare/demo/fhir/r4"
AUTH = ("_SYSTEM", "ISCDEMO")

# IRIS SQL REST API Settings
IRIS_SQL_URL = "http://localhost:32783/api/atelier/v1/DEMO/action/query"

def execute_sql(sql_query):
    """Execute SQL query via IRIS REST API"""
    payload = {
        "query": sql_query
    }
    response = requests.post(
        IRIS_SQL_URL,
        json=payload,
        auth=AUTH,
        headers={"Content-Type": "application/json"}
    )
    return response.json() if response.status_code == 200 else None

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

def main():
    print("IRIS Vector Search Demo (Simplified)\n")
    print("=" * 80)
    
    # 1. Load embedding model
    print("\n📥 Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ Model loaded (384-dimensional embeddings)\n")
    
    # 2. Fetch FHIR data
    print("📊 Fetching FHIR data from server...")
    
    # Get observations
    observations_url = f"{FHIR_URL}/Observation?patient=Patient/pat-1"
    obs_response = requests.get(observations_url, auth=AUTH)
    
    clinical_data = []
    
    if obs_response.status_code == 200:
        bundle = obs_response.json()
        for entry in bundle.get('entry', []):
            resource = entry['resource']
            text = extract_text_from_observation(resource)
            clinical_data.append({
                'type': 'Observation',
                'id': resource['id'],
                'text': text
            })
            print(f"  ✅ Observation: {text[:60]}...")
    
    # Get ServiceRequests
    sr_url = f"{FHIR_URL}/ServiceRequest?patient=Patient/pat-1"
    sr_response = requests.get(sr_url, auth=AUTH)
    
    if sr_response.status_code == 200:
        bundle = sr_response.json()
        for entry in bundle.get('entry', []):
            resource = entry['resource']
            text = extract_text_from_service_request(resource)
            if text:
                clinical_data.append({
                    'type': 'ServiceRequest',
                    'id': resource['id'],
                    'text': text
                })
                print(f"  ✅ ServiceRequest: {text[:60]}...")
    
    print(f"\n📝 Total clinical notes collected: {len(clinical_data)}\n")
    
    # 3. Generate embeddings
    print("🧮 Generating embeddings...")
    for item in clinical_data:
        embedding = model.encode(item['text'])
        item['embedding'] = embedding
        print(f"  ✅ Generated embedding for {item['type']}/{item['id']}")
    
    print(f"\n✅ All embeddings generated (shape: 384-dimensional vectors)\n")
    
    # 4. Demonstrate vector similarity search (in-memory)
    print("=" * 80)
    print("VECTOR SIMILARITY SEARCH EXAMPLES")
    print("=" * 80)
    
    def search(query_text, top_k=3):
        """Perform in-memory vector similarity search"""
        print(f"\n🔍 Query: '{query_text}'")
        print("-" * 80)
        
        # Generate query embedding
        query_embedding = model.encode(query_text)
        
        # Calculate similarities (cosine similarity via dot product of normalized vectors)
        import numpy as np
        
        results = []
        for item in clinical_data:
            # Normalize vectors
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            item_norm = item['embedding'] / np.linalg.norm(item['embedding'])
            
            # Dot product of normalized vectors = cosine similarity
            similarity = np.dot(query_norm, item_norm)
            
            results.append({
                'item': item,
                'similarity': similarity
            })
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Show top results
        for i, result in enumerate(results[:top_k], 1):
            print(f"\n{i}. Similarity: {result['similarity']:.4f}")
            print(f"   Resource: {result['item']['type']}/{result['item']['id']}")
            print(f"   Text: {result['item']['text']}")
    
    # Example searches
    search("tumor and pathology findings", top_k=2)
    search("patient symptoms and complaints", top_k=2)
    search("planned medical imaging procedures", top_k=2)
    
    # 5. Show how to store in IRIS (SQL example)
    print("\n\n" + "=" * 80)
    print("HOW TO STORE IN IRIS")
    print("=" * 80)
    
    print("""
To store these embeddings in IRIS for persistent vector search:

1. Create a table with VECTOR column:
   
   CREATE TABLE ClinicalNotes (
       id INTEGER PRIMARY KEY,
       fhir_resource_type VARCHAR(50),
       fhir_resource_id VARCHAR(50),
       patient_id VARCHAR(50),
       text_content VARCHAR(5000),
       embedding VECTOR(DECIMAL, 384)
   )

2. Insert data with embeddings:
   
   INSERT INTO ClinicalNotes 
   (id, fhir_resource_type, fhir_resource_id, patient_id, text_content, embedding)
   VALUES (1, 'Observation', '3881', 'pat-1', 'Histology...', 
           TO_VECTOR('[0.123, -0.456, ...]'))

3. Query using vector similarity:
   
   SELECT TOP 5
       fhir_resource_type,
       fhir_resource_id,
       text_content,
       VECTOR_DOT_PRODUCT(embedding, TO_VECTOR('[query_vector]')) as similarity
   FROM ClinicalNotes
   ORDER BY similarity DESC

4. Access via Python using intersystems_iris package or REST API
""")
    
    print("\n✅ Demo complete!")
    print("\nNote: This demo performed in-memory search. For production, store")
    print("embeddings in IRIS tables for persistent, scalable vector search.")

if __name__ == "__main__":
    main()
