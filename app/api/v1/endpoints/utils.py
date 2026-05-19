from fastapi import HTTPException


def ensure_found(found: bool, resource: str) -> None:
    if not found:
        raise HTTPException(status_code=404, detail=f"{resource} not found")
