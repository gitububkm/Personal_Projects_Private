import uuid
from typing import List
from fastapi import APIRouter, status, Query
from app.schemas.comment import CommentCreate, CommentResponse, CommentUpdate
from app.api.dependencies import CommentServiceDep, CommentRepoDep

router = APIRouter(prefix="/comments", tags=["comments"])

@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(comment_data: CommentCreate, service: CommentServiceDep):
    return await service.create_comment(comment_data)

@router.get("/", response_model=List[CommentResponse])
async def list_comments(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), comment_repo: CommentRepoDep = None):
    return await comment_repo.get_multi(skip=skip, limit=limit)

@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(comment_id: uuid.UUID, service: CommentServiceDep):
    return await service.get_by_id(comment_id)

@router.patch("/{comment_id}", response_model=CommentResponse)
async def update_comment_partial(comment_id: uuid.UUID, comment_data: CommentUpdate, service: CommentServiceDep):
    return await service.update_comment(comment_id, comment_data)

@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: uuid.UUID, service: CommentServiceDep):
    await service.delete_comment(comment_id)
