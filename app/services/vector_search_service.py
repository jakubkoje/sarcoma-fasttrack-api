"""
Vector Search Service for IRIS Database
Handles storing and searching embeddings in IRIS
"""
import requests
import json
from typing import List, Dict, Optional, Tuple
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def execute_iris_sql(sql_query: str) -> Optional[Dict]:
    """Execute SQL query via IRIS REST API"""
    try:
        payload = {"query": sql_query}
        response = requests.post(
            settings.IRIS_SQL_URL,
            json=payload,
            auth=(settings.IRIS_USERNAME, settings.IRIS_PASSWORD),
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"IRIS SQL query failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception executing IRIS SQL: {e}")
        return None


def store_report_embedding(
    report_id: int,
    fhir_id: Optional[str],
    report_text: str,
    embedding: List[float],
    specialist: Optional[str] = None,
    severity: Optional[str] = None,
    confidence: Optional[float] = None
) -> bool:
    """
    Store report embedding in IRIS
    
    Args:
        report_id: Internal report ID
        fhir_id: FHIR ServiceRequest ID
        report_text: Extracted report text
        embedding: 384-dimensional embedding vector
        specialist: Classified specialist type
        severity: Classified severity level
        confidence: Classification confidence score
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Convert embedding list to IRIS vector format
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        
        # Escape single quotes in text
        safe_text = report_text.replace("'", "''")
        safe_fhir_id = fhir_id.replace("'", "''") if fhir_id else "NULL"
        
        sql = f"""
        INSERT INTO ReportEmbeddings 
        (report_id, fhir_service_request_id, report_text, embedding, 
         specialist_classification, severity_classification, classification_confidence)
        VALUES (
            {report_id},
            '{safe_fhir_id}',
            '{safe_text}',
            TO_VECTOR('{embedding_str}'),
            '{specialist}' if specialist else 'NULL',
            '{severity}' if severity else 'NULL',
            {confidence if confidence else 'NULL'}
        )
        """
        
        result = execute_iris_sql(sql)
        return result is not None
        
    except Exception as e:
        logger.error(f"Error storing report embedding: {e}")
        return False


def find_similar_specialists(embedding: List[float], top_k: int = 5) -> List[Dict]:
    """
    Find most similar specialist examples using vector search
    
    Args:
        embedding: Query embedding vector
        top_k: Number of top results to return
        
    Returns:
        List of dicts with specialist_type and similarity score
    """
    try:
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        
        sql = f"""
        SELECT TOP {top_k}
            specialist_type,
            example_text,
            VECTOR_DOT_PRODUCT(embedding, TO_VECTOR('{embedding_str}')) as similarity
        FROM SpecialistExamples
        ORDER BY similarity DESC
        """
        
        result = execute_iris_sql(sql)
        
        if result and 'result' in result and 'content' in result['result']:
            rows = result['result']['content']
            return [
                {
                    'specialist_type': row[0],
                    'example_text': row[1],
                    'similarity': float(row[2])
                }
                for row in rows
            ]
        
        return []
        
    except Exception as e:
        logger.error(f"Error finding similar specialists: {e}")
        return []


def find_similar_severity(embedding: List[float], top_k: int = 5) -> List[Dict]:
    """
    Find most similar severity examples using vector search
    
    Args:
        embedding: Query embedding vector
        top_k: Number of top results to return
        
    Returns:
        List of dicts with severity_level, severity_code and similarity score
    """
    try:
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        
        sql = f"""
        SELECT TOP {top_k}
            severity_level,
            severity_code,
            example_text,
            VECTOR_DOT_PRODUCT(embedding, TO_VECTOR('{embedding_str}')) as similarity
        FROM SeverityExamples
        ORDER BY similarity DESC
        """
        
        result = execute_iris_sql(sql)
        
        if result and 'result' in result and 'content' in result['result']:
            rows = result['result']['content']
            return [
                {
                    'severity_level': row[0],
                    'severity_code': int(row[1]),
                    'example_text': row[2],
                    'similarity': float(row[3])
                }
                for row in rows
            ]
        
        return []
        
    except Exception as e:
        logger.error(f"Error finding similar severity: {e}")
        return []


def get_report_classification(report_id: int) -> Optional[Dict]:
    """
    Retrieve stored classification for a report
    
    Args:
        report_id: Internal report ID
        
    Returns:
        Dict with classification info or None
    """
    try:
        sql = f"""
        SELECT 
            specialist_classification,
            severity_classification,
            classification_confidence
        FROM ReportEmbeddings
        WHERE report_id = {report_id}
        """
        
        result = execute_iris_sql(sql)
        
        if result and 'result' in result and 'content' in result['result']:
            rows = result['result']['content']
            if rows:
                return {
                    'specialist': rows[0][0],
                    'severity': rows[0][1],
                    'confidence': float(rows[0][2]) if rows[0][2] else None
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Error retrieving report classification: {e}")
        return None
