from fastapi import FastAPI
from contextlib import asynccontextmanager

from api.routes import router
from api.rls_test_routes import router as rls_test_router
from api.chatbot_routes import router as chatbot_router
from db.pool import close_pool, init_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    pool = await init_pool()
    app.state.pool = pool

    yield

    # Shutdown
    await close_pool()
    app.state.pool = None


def create_app() -> FastAPI:
    application = FastAPI(
        title="SR Service (FastAPI)",
        lifespan=lifespan
    )

    application.include_router(router)
    application.include_router(rls_test_router)
    application.include_router(chatbot_router)

    return application


app = create_app()


__all__ = ["app", "create_app"]