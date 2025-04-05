from fastapi import APIRouter
from apps.users.routers import router as users_router

v1_router = APIRouter()
v1_router.include_router(users_router)