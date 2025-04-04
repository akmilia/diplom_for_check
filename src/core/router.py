from fastapi import APIRouter

from apps.users.routers import router as users_router

v1_router = APIRouter(prefix='/v1')
v1_router.include_router(users_router, prefix="/users")
