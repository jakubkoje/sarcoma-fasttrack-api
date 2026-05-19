from fastapi import APIRouter
from fastapi import Depends
from app.api.deps import require_user
from app.api.v1.endpoints import auth, patients, reports, users, organizations

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(patients.router, dependencies=[Depends(require_user)])
api_router.include_router(reports.router, dependencies=[Depends(require_user)])
api_router.include_router(organizations.router, dependencies=[Depends(require_user)])
