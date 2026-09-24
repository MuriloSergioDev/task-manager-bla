from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.presentation.api.routes import auth, health, tasks


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(title="Task Management API", version="0.1.0")

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.state.limiter = limiter
    application.add_exception_handler(
        RateLimitExceeded,
        _rate_limit_exceeded_handler,  # type: ignore[arg-type]
    )
    application.add_middleware(SlowAPIMiddleware)

    application.include_router(health.router)
    application.include_router(auth.router)
    application.include_router(tasks.router)

    return application


app = create_app()
