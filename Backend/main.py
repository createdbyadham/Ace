from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from api.flashcard_routes import router as flashcard_router
from api.rls_test_routes import router as rls_test_router
from api.chatbot_routes import router as chatbot_router
from api.agent_routes import router as agent_router
from api.question_routes import router as question_router
from api.file_routes import router as file_router
from api.summary_routes import router as summary_router
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
        title="Ace Backend (FastAPI)",
        lifespan=lifespan
    )

    # Enable CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(flashcard_router)
    application.include_router(question_router)
    application.include_router(router)
    application.include_router(rls_test_router)
    application.include_router(chatbot_router)
    application.include_router(agent_router)
    application.include_router(file_router)
    application.include_router(summary_router)
    

    return application


app = create_app()


__all__ = ["app", "create_app"]