import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.services.scheduler import start_scheduler, stop_scheduler
from app.services.ws import hub


@asynccontextmanager
async def lifespan(app: FastAPI):
    hub.set_loop(asyncio.get_running_loop())
    bootstrap_schema()
    if settings.scheduler_enabled:
        start_scheduler()
    yield
    stop_scheduler()


def bootstrap_schema() -> None:
    """Dev bootstrap: create the schema + seed once if Alembic was never run.

    Alembic stays the source of truth for schema evolution; this only fires
    when the `users` table is missing entirely (fresh database).
    """
    if not settings.auto_create_tables:
        return
    try:
        from sqlalchemy import inspect

        from app.core.database import Base, engine
        import app.models  # noqa: F401

        if inspect(engine).has_table("users"):
            return
        Base.metadata.create_all(engine)
        from app.seed import seed

        seed()
        print("bootstrap: schema created and seeded (alembic not applied yet)")
    except Exception as exc:  # noqa: BLE001 — never block startup on bootstrap
        print(f"bootstrap skipped: {exc}")


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}
