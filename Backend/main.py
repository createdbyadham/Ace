from fastapi import FastAPI

from api.routes import router
from api.rls_test_routes import router as rls_test_router
from db.pool import close_pool, init_pool


def create_app() -> FastAPI:
    application = FastAPI(title="SR Service (FastAPI)")
    application.include_router(router)
    application.include_router(rls_test_router)

    @application.on_event("startup")
    async def on_startup() -> None:
        pool = await init_pool()
        application.state.pool = pool

    @application.on_event("shutdown")
    async def on_shutdown() -> None:
        await close_pool()
        application.state.pool = None

    return application


app = create_app()


__all__ = ["app", "create_app"]

