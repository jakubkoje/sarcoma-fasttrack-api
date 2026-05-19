"""
Classification Service for Reports
Classifies reports by specialist type and severity using vector search
"""
from typing import Dict, Tuple
from app.services.embedding_service import generate_embedding, extract_report_text
from app.services.vector_search_service import (
    find_similar_specialists,
    find_similar_severity,
    store_report_embedding
)
import logging
from collections import Counter

logger = logging.getLogger(__name__)


def classify_specialist(embedding: list) -> Tuple[str, float]:
    """
    Classify which specialist should review the report
    
    Args:
        embedding: Report embedding vector
        
    Returns:
        Tuple of (specialist_type, confidence_score)
    """
    # Find top 5 most similar specialist examples
    similar = find_similar_specialists(embedding, top_k=5)
    
    if not similar:
        logger.warning("No specialist examples found, defaulting to oncologist")
        return ("oncologist", 0.5)
    
    # Count votes from top matches (weighted by similarity)
    votes = {}
    total_similarity = 0.0
    
    for match in similar:
        specialist = match['specialist_type']
        similarity = match['similarity']
        
        if specialist not in votes:
            votes[specialist] = 0.0
        votes[specialist] += similarity
        total_similarity += similarity
    
    # Get specialist with highest weighted vote
    best_specialist = max(votes.items(), key=lambda x: x[1])
    specialist_type = best_specialist[0]
    confidence = best_specialist[1] / total_similarity if total_similarity > 0 else 0.5
    
    logger.info(f"Classified as {specialist_type} with confidence {confidence:.2f}")
    return (specialist_type, confidence)


def classify_severity(embedding: list) -> Tuple[str, int, float]:
    """
    Classify the severity level of the report
    
    Args:
        embedding: Report embedding vector
        
    Returns:
        Tuple of (severity_level, severity_code, confidence_score)
    """
    # Find top 5 most similar severity examples
    similar = find_similar_severity(embedding, top_k=5)
    
    if not similar:
        logger.warning("No severity examples found, defaulting to medium")
        return ("medium", 2, 0.5)
    
    # Count votes from top matches (weighted by similarity)
    votes = {}
    total_similarity = 0.0
    
    for match in similar:
        severity = match['severity_level']
        code = match['severity_code']
        similarity = match['similarity']
        
        if severity not in votes:
            votes[severity] = {'code': code, 'score': 0.0}
        votes[severity]['score'] += similarity
        total_similarity += similarity
    
    # Get severity with highest weighted vote
    best_severity = max(votes.items(), key=lambda x: x[1]['score'])
    severity_level = best_severity[0]
    severity_code = best_severity[1]['code']
    confidence = best_severity[1]['score'] / total_similarity if total_similarity > 0 else 0.5
    
    logger.info(f"Classified as {severity_level} (code {severity_code}) with confidence {confidence:.2f}")
    return (severity_level, severity_code, confidence)


def classify_report(report_id: int, report_data: dict, fhir_id: str = None) -> Dict:
    """
    Main classification function for a report
    
    Args:
        report_id: Internal report ID
        report_data: Dictionary with report fields
        fhir_id: Optional FHIR ServiceRequest ID
        
    Returns:
        Dictionary with classification results:
        {
            "specialist": "oncologist",
            "specialist_confidence": 0.85,
            "severity": "critical",
            "severity_code": 1,
            "severity_confidence": 0.92,
            "overall_confidence": 0.88
        }
    """
    try:
        # Extract text from report
        report_text = extract_report_text(report_data)
        logger.info(f"Extracted text from report {report_id}: {report_text[:100]}...")
        
        # Generate embedding
        embedding = generate_embedding(report_text)
        logger.info(f"Generated embedding for report {report_id}")
        
        # Classify specialist
        specialist, specialist_conf = classify_specialist(embedding)
        
        # Classify severity
        severity, severity_code, severity_conf = classify_severity(embedding)
        
        # Calculate overall confidence
        overall_conf = (specialist_conf + severity_conf) / 2
        
        # Store in IRIS
        store_success = store_report_embedding(
            report_id=report_id,
            fhir_id=fhir_id,
            report_text=report_text,
            embedding=embedding,
            specialist=specialist,
            severity=severity,
            confidence=overall_conf
        )
        
        if not store_success:
            logger.warning(f"Failed to store embedding for report {report_id}")
        
        return {
            "specialist": specialist,
            "specialist_confidence": round(specialist_conf, 4),
            "severity": severity,
            "severity_code": severity_code,
            "severity_confidence": round(severity_conf, 4),
            "overall_confidence": round(overall_conf, 4)
        }
        
    except Exception as e:
        logger.error(f"Error classifying report {report_id}: {e}")
        # Return default classification on error
        return {
            "specialist": "oncologist",
            "specialist_confidence": 0.5,
            "severity": "medium",
            "severity_code": 2,
            "severity_confidence": 0.5,
            "overall_confidence": 0.5,
            "error": str(e)
        }
