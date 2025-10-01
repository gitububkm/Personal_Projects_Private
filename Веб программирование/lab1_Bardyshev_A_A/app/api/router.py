from fastapi import APIRouter
from .v1 import users, news, comments

api_router = APIRouter(prefix="/api")
v1_router = APIRouter(prefix="/v1")

v1_router.include_router(users.router)
v1_router.include_router(news.router)
v1_router.include_router(comments.router)

api_router.include_router(v1_router)
