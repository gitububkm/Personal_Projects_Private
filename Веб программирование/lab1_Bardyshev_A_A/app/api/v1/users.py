import uuid
from typing import List
from fastapi import APIRouter, status, Query
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.api.dependencies import UserServiceDep, UserRepoDep

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, service: UserServiceDep):
    return await service.create_user(user_data)

@router.get("/", response_model=List[UserResponse])
async def list_users(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), user_repo: UserRepoDep = None):
    return await user_repo.get_multi(skip=skip, limit=limit)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: uuid.UUID, service: UserServiceDep):
    return await service.get_by_id(user_id)

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user_partial(user_id: uuid.UUID, user_data: UserUpdate, service: UserServiceDep):
    return await service.update_user(user_id, user_data)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: uuid.UUID, service: UserServiceDep):
    await service.delete_user(user_id)
