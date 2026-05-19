"""
FHIR Data Extraction Utilities
Functions to extract structured data from FHIR resource JSON
"""
from typing import Optional, Dict, Any


def extract_patient_data(fhir_resource: Dict[str, Any]) -> Dict[str, Any]:
    """Extract patient demographic data from FHIR Patient resource"""
    data = {
        "first_name": None,
        "last_name": None,
        "address": None,
        "birth_number": None,
        "phone": None,
        "email": None,
        "managing_org_id": None,
    }
    
    if not fhir_resource:
        return data
    
    # Extract name
    if fhir_resource.get("name") and len(fhir_resource["name"]) > 0:
        name = fhir_resource["name"][0]
        if name.get("given"):
            data["first_name"] = name["given"][0] if isinstance(name["given"], list) else name["given"]
        if name.get("family"):
            data["last_name"] = name["family"]
    
    # Extract address
    if fhir_resource.get("address") and len(fhir_resource["address"]) > 0:
        address = fhir_resource["address"][0]
        if address.get("text"):
            data["address"] = address["text"]
    
    # Extract identifier (birth number)
    if fhir_resource.get("identifier"):
        for identifier in fhir_resource["identifier"]:
            if identifier.get("system") == "urn:oid:1.2.203.24341.1.1.1":
                data["birth_number"] = identifier.get("value")
                break
    
    # Extract telecom (phone and email)
    if fhir_resource.get("telecom"):
        for telecom in fhir_resource["telecom"]:
            system = telecom.get("system", "")
            value = telecom.get("value")
            if system == "phone" and value:
                data["phone"] = value
            elif system == "email" and value:
                data["email"] = value
    
    # Extract managing organization
    if fhir_resource.get("managingOrganization"):
        managing_org = fhir_resource["managingOrganization"]
        if managing_org.get("reference"):
            # Extract ID from reference like "Organization/org-123"
            ref = managing_org["reference"]
            if "/" in ref:
                data["managing_org_id"] = ref.split("/")[-1]
    
    return data


def extract_organization_data(fhir_resource: Dict[str, Any]) -> Dict[str, Any]:
    """Extract organization data from FHIR Organization resource"""
    data = {
        "name": None,
        "type_code": None,
        "address": None,
        "contact": None,
    }
    
    if not fhir_resource:
        return data
    
    # Extract name
    data["name"] = fhir_resource.get("name")
    
    # Extract type
    if fhir_resource.get("type") and len(fhir_resource["type"]) > 0:
        org_type = fhir_resource["type"][0]
        if org_type.get("coding") and len(org_type["coding"]) > 0:
            data["type_code"] = org_type["coding"][0].get("code")
    
    # Extract address
    if fhir_resource.get("address") and len(fhir_resource["address"]) > 0:
        address = fhir_resource["address"][0]
        if address.get("text"):
            data["address"] = address["text"]
    
    # Extract telecom (contact)
    if fhir_resource.get("telecom") and len(fhir_resource["telecom"]) > 0:
        telecom = fhir_resource["telecom"][0]
        if telecom.get("system") == "phone":
            data["contact"] = telecom.get("value")
    
    return data


def extract_service_request_data(service_request: dict) -> dict:
    """
    Extract data from a FHIR ServiceRequest resource.
    Parses all custom extensions and standard FHIR fields.
    
    Args:
        service_request: FHIR ServiceRequest resource as dict
        
    Returns:
        Dictionary with extracted data
    """
    data = {}
    
    # Extract authoredOn (creation date)
    if "authoredOn" in service_request:
        data["authored_on"] = service_request["authoredOn"]
    
    # Extract note
    if "note" in service_request and service_request["note"]:
        notes = [note.get("text", "") for note in service_request["note"]]
        data["note"] = " | ".join(notes) if notes else None
    
    # Extract MKN-10 code from reasonCode
    if "reasonCode" in service_request and service_request["reasonCode"]:
        for reason in service_request["reasonCode"]:
            if "coding" in reason:
                for coding in reason["coding"]:
                    if coding.get("system") == "http://hl7.org/fhir/sid/icd-10":
                        data["mkn10_code"] = coding.get("code")
                        break
    
    # Extract all custom extensions
    if "extension" in service_request and service_request["extension"]:
        base_url = "http://sarcomfasttrack.cz/fhir/StructureDefinition"
        
        for ext in service_request["extension"]:
            url = ext.get("url", "")
            
            # Map extension URLs to field names
            if url == f"{base_url}/is-new-patient":
                data["is_new_patient"] = ext.get("valueBoolean")
            elif url == f"{base_url}/anamnesis":
                data["anamnesis"] = ext.get("valueString")
            elif url == f"{base_url}/family-history":
                data["family_history"] = ext.get("valueString")
            elif url == f"{base_url}/any-imaging-performed":
                data["any_imaging_performed"] = ext.get("valueBoolean")
            elif url == f"{base_url}/additional-imaging-planned":
                data["additional_imaging_planned"] = ext.get("valueBoolean")
            elif url == f"{base_url}/additional-imaging-note":
                data["additional_imaging_note"] = ext.get("valueString")
            elif url == f"{base_url}/anticoagulant-medication":
                data["anticoagulant_medication"] = ext.get("valueBoolean")
            elif url == f"{base_url}/anticoagulant-detail":
                data["anticoagulant_detail"] = ext.get("valueString")
            elif url == f"{base_url}/histology-performed":
                data["histology_performed"] = ext.get("valueBoolean")
            elif url == f"{base_url}/histology-date":
                data["histology_date"] = ext.get("valueDate")
            elif url == f"{base_url}/histology-result":
                data["histology_result"] = ext.get("valueString")
            elif url == f"{base_url}/summary":
                data["summary"] = ext.get("valueString")
            elif url == f"{base_url}/feedback-specialist":
                data["feedback_specialist"] = ext.get("valueString")
            elif url == f"{base_url}/attachment-path":
                data["attachment_path"] = ext.get("valueString")
            elif url == f"{base_url}/specialist":
                data["specialist"] = ext.get("valueString")
            elif url == f"{base_url}/severity":
                data["severity"] = ext.get("valueString")
            
    
    return data


def extract_practitioner_data(fhir_resource: Dict[str, Any]) -> Dict[str, Any]:
    """Extract practitioner data from FHIR Practitioner resource"""
    data = {
        "name": None,
    }
    
    if not fhir_resource:
        return data
    
    # Extract name
    if fhir_resource.get("name") and len(fhir_resource["name"]) > 0:
        name = fhir_resource["name"][0]
        if name.get("text"):
            data["name"] = name["text"]
        elif name.get("given") or name.get("family"):
            parts = []
            if name.get("given"):
                parts.extend(name["given"] if isinstance(name["given"], list) else [name["given"]])
            if name.get("family"):
                parts.append(name["family"])
            data["name"] = " ".join(parts)
    
    return data
