from fastapi import FastAPI
from .api.router import api_router

app = FastAPI(title="News CRUD API")

@app.get("/")
async def root():
    return {"status": "ok", "message": "Welcome to News CRUD API"}

app.include_router(api_router)
