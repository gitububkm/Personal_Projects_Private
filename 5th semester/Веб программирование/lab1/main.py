import os
import time
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.routers import users_router, news_router, comments_router, auth_router
from src.logging_config import setup_logging
from src.hawk_integration import hawk_client, capture_exception
from src.metrics import metrics_exporter

import structlog
from prometheus_fastapi_instrumentator import Instrumentator

# Настройка логирования
logger = setup_logging()


async def save_metrics_periodically():
    """Периодически сохраняет метрики в JSON файл"""
    while True:
        try:
            await asyncio.sleep(30)  # Каждые 30 секунд
            metrics_exporter.save_metrics_to_file()
        except Exception as e:
            logger.error("Failed to save metrics", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    task = asyncio.create_task(save_metrics_periodically())
    logger.info("Application started")
    yield
    # Shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("Application stopped")


app = FastAPI(
    title="News API",
    description="CRUD API для управления пользователями, новостями и комментариями с авторизацией",
    version="2.0.0",
    lifespan=lifespan
)

# --- MIDDLEWARES ---

# Hawk Middleware
@app.middleware("http")
async def hawk_exception_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        if hawk_client:
            capture_exception(e)
        raise e


# Logging Middleware
@app.middleware("http")
async def structlog_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", "unknown")

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else "unknown",
    )

    start_time = time.perf_counter_ns()

    try:
        response = await call_next(request)
        process_time = (time.perf_counter_ns() - start_time) / 10**6  # ms

        structlog.contextvars.bind_contextvars(
            status_code=response.status_code,
            process_time=process_time,
        )

        if 400 <= response.status_code < 500:
            logger.warning("Client error")
        elif response.status_code >= 500:
            logger.error("Server error")
        else:
            logger.info("Request processed")

        return response
    except Exception as e:
        logger.exception("Request failed", error=str(e))
        raise e


# --- PROMETHEUS SETUP ---
Instrumentator().instrument(app)


# --- EXCEPTION HANDLERS ---

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик всех исключений"""
    logger.exception("unhandled_exception", error=str(exc), error_type=type(exc).__name__)
    
    if hawk_client:
        capture_exception(exc)
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Обработчик HTTP исключений"""
    logger.warning("http_exception", status_code=exc.status_code, detail=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Обработчик ошибок валидации"""
    logger.warning("validation_error", errors=exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )


# --- ROUTES ---
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(news_router)
app.include_router(comments_router)


@app.get("/")
def root():
    logger.info("root_endpoint_accessed")
    return {
        "message": "News API",
        "docs": "/docs",
        "redoc": "/redoc",
        "metrics": "/metrics"
    }


@app.get("/error_test")
def error_test():
    """Тестовый эндпоинт для генерации ошибки (для тестирования Hawk)"""
    raise ValueError("This is a test error for Hawk verification!")


if __name__ == "__main__":
    import uvicorn
    logger.info("starting_server", host="0.0.0.0", port=8000)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

