from fastapi import APIRouter
from backend.app.api.v1.endpoints import health, policies, complaints, agents

api_v1_router = APIRouter()

# Include endpoint routers
api_v1_router.include_router(health.router)
api_v1_router.include_router(policies.router)
api_v1_router.include_router(complaints.router)
api_v1_router.include_router(agents.router)
