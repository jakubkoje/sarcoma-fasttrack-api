"""
FHIR Client Utility for uploading resources to FHIR server
"""

import requests
from typing import Optional, Dict, Any
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def upload_fhir_resource(resource) -> Optional[str]:
    """
    Upload a FHIR resource with a specific ID using PUT.
    Returns the FHIR resource ID if successful, None otherwise.

    Args:
        resource: A FHIR resource object from fhir.resources library

    Returns:
        str: The FHIR resource ID if successful, None otherwise
    """
    if not settings.FHIR_ENABLED:
        logger.warning("FHIR is disabled; skipping upload.")
        return None

    try:
        # fhir.resources models usually have resourceType field, or we can use class name
        try:
            resource_type = resource.resourceType
        except AttributeError:
            resource_type = resource.__class__.__name__
        resource_id = resource.id

        url = f"{settings.FHIR_SERVER_URL}/{resource_type}/{resource_id}"

        logger.info(f"Uploading {resource_type}/{resource_id} to FHIR server...")

        response = requests.put(
            url,
            data=resource.json(),
            auth=(settings.FHIR_SERVER_USER, settings.FHIR_SERVER_PASSWORD),
            headers={"Content-Type": "application/fhir+json"},
            timeout=10,
        )

        if response.status_code in [200, 201]:
            logger.info(f"✅ Successfully uploaded {resource_type}/{resource_id}")
            return resource_id
        else:
            logger.error(
                f"❌ Failed to upload {resource_type}/{resource_id}: {response.status_code}"
            )
            logger.error(response.text)
            return None

    except Exception as e:
        logger.error(f"Exception uploading FHIR resource: {e}")
        return None


def create_fhir_resource(resource) -> Optional[str]:
    """
    Create a FHIR resource without a specific ID using POST.
    Returns the FHIR resource ID assigned by the server if successful, None otherwise.

    Args:
        resource: A FHIR resource object from fhir.resources library

    Returns:
        str: The FHIR resource ID assigned by server if successful, None otherwise
    """
    if not settings.FHIR_ENABLED:
        logger.warning("FHIR is disabled; skipping create.")
        return None

    try:
        # fhir.resources models usually have resourceType field, or we can use class name
        try:
            resource_type = resource.resourceType
        except AttributeError:
            resource_type = resource.__class__.__name__

        url = f"{settings.FHIR_SERVER_URL}/{resource_type}"

        logger.info(f"Creating new {resource_type} on FHIR server...")

        response = requests.post(
            url,
            data=resource.json(),
            auth=(settings.FHIR_SERVER_USER, settings.FHIR_SERVER_PASSWORD),
            headers={"Content-Type": "application/fhir+json"},
            timeout=10,
        )

        if response.status_code in [200, 201]:
            try:
                resp_json = response.json()
                resource_id = resp_json.get("id")
                logger.info(
                    f"✅ Successfully created {resource_type} with ID: {resource_id}"
                )
                return resource_id
            except Exception:
                # If no body, check Location header
                location = response.headers.get("Location")
                if location:
                    # Extract ID from location header
                    resource_id = location.split("/")[-1].split("/_history")[0]
                    logger.info(
                        f"✅ Successfully created {resource_type} with ID: {resource_id}"
                    )
                    return resource_id
                logger.warning(f"Created {resource_type} but couldn't extract ID")
                return None
        else:
            logger.error(f"❌ Failed to create {resource_type}: {response.status_code}")
            logger.error(response.text)
            return None

    except Exception as e:
        logger.error(f"Exception creating FHIR resource: {e}")
        return None


def get_fhir_resource(resource_type: str, resource_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a FHIR resource from the FHIR server.

    Args:
        resource_type: The type of FHIR resource (e.g., "Patient", "Organization")
        resource_id: The ID of the resource to retrieve

    Returns:
        dict: The FHIR resource as a dictionary if successful, None otherwise
    """
    if not settings.FHIR_ENABLED:
        logger.warning("FHIR is disabled; skipping fetch.")
        return None

    try:
        url = f"{settings.FHIR_SERVER_URL}/{resource_type}/{resource_id}"

        logger.info(f"Retrieving {resource_type}/{resource_id} from FHIR server...")

        response = requests.get(
            url,
            auth=(settings.FHIR_SERVER_USER, settings.FHIR_SERVER_PASSWORD),
            headers={"Content-Type": "application/fhir+json"},
            timeout=10,
        )

        if response.status_code == 200:
            logger.info(f"✅ Successfully retrieved {resource_type}/{resource_id}")
            return response.json()
        else:
            logger.error(
                f"❌ Failed to retrieve {resource_type}/{resource_id}: {response.status_code}"
            )
            return None

    except Exception as e:
        logger.error(f"Exception retrieving FHIR resource: {e}")
        return None
