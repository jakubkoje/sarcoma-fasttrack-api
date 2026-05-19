"""
Embedding Service for generating vector embeddings from text
Uses sentence-transformers (all-MiniLM-L6-v2) for 384-dimensional embeddings
"""
from sentence_transformers import SentenceTransformer
from typing import List
import logging

logger = logging.getLogger(__name__)

# Global model instance (loaded once)
_model = None


def get_embedding_model() -> SentenceTransformer:
    """Get or initialize the embedding model (singleton pattern)"""
    global _model
    if _model is None:
        logger.info("Loading sentence-transformers model (all-MiniLM-L6-v2)...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ Embedding model loaded (384 dimensions)")
    return _model


def generate_embedding(text: str) -> List[float]:
    """
    Generate a 384-dimensional embedding vector from text
    
    Args:
        text: Input text to embed
        
    Returns:
        List of 384 float values representing the embedding
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for embedding")
        return [0.0] * 384  # Return zero vector for empty text
    
    model = get_embedding_model()
    embedding = model.encode(text)
    return embedding.tolist()


def extract_report_text(report_data) -> str:
    """
    Extract meaningful text from a report for embedding
    
    Args:
        report_data: Report object (SQLModel) or dictionary containing report fields
        
    Returns:
        Combined text string for embedding
    """
    text_parts = []
    
    # Convert SQLModel to dict if needed
    if hasattr(report_data, 'model_dump'):
        report_dict = report_data.model_dump()
    elif hasattr(report_data, '__dict__'):
        report_dict = report_data.__dict__
    else:
        report_dict = report_data
    
    # Add various report fields
    if report_dict.get('anamnesis'):
        text_parts.append(f"Anamnesis: {report_dict['anamnesis']}")
    
    if report_dict.get('family_history'):
        text_parts.append(f"Family History: {report_dict['family_history']}")
    
    if report_dict.get('histology_result'):
        text_parts.append(f"Histology: {report_dict['histology_result']}")
    
    if report_dict.get('summary'):
        text_parts.append(f"Summary: {report_dict['summary']}")
    
    if report_dict.get('additional_imaging_note'):
        text_parts.append(f"Imaging Notes: {report_dict['additional_imaging_note']}")
    
    if report_dict.get('anticoagulant_detail'):
        text_parts.append(f"Anticoagulant: {report_dict['anticoagulant_detail']}")
    
    if report_dict.get('mkn10_code'):
        text_parts.append(f"Diagnosis Code: {report_dict['mkn10_code']}")
    
    if report_dict.get('feedback_specialist'):
        text_parts.append(f"Specialist Feedback: {report_dict['feedback_specialist']}")
    
    # Join all parts
    combined_text = " | ".join(text_parts)
    
    if not combined_text:
        logger.warning("No meaningful text extracted from report")
        return "No clinical information provided"
    
    return combined_text
