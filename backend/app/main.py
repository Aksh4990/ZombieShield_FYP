from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401 - registers SQLAlchemy models


@asynccontextmanager
async def lifespan(_: FastAPI):
    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE IF EXISTS apis ADD COLUMN IF NOT EXISTS sources JSONB NOT NULL DEFAULT '[]'::jsonb")
            connection.exec_driver_sql("ALTER TABLE IF EXISTS apis ADD COLUMN IF NOT EXISTS canonical_key VARCHAR(64)")
            connection.exec_driver_sql("ALTER TABLE IF EXISTS apis ADD COLUMN IF NOT EXISTS is_deprecated BOOLEAN NOT NULL DEFAULT FALSE")
            connection.exec_driver_sql("ALTER TABLE IF EXISTS apis ADD COLUMN IF NOT EXISTS is_removed_from_supported_surface BOOLEAN NOT NULL DEFAULT FALSE")
            connection.exec_driver_sql("ALTER TABLE IF EXISTS apis ADD COLUMN IF NOT EXISTS classification_reason VARCHAR(1000)")
            connection.exec_driver_sql("ALTER TABLE IF EXISTS apis ADD COLUMN IF NOT EXISTS classified_at TIMESTAMPTZ")
    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.exec_driver_sql("UPDATE apis SET sources = jsonb_build_array(source) WHERE sources = '[]'::jsonb")
            connection.exec_driver_sql("CREATE UNIQUE INDEX IF NOT EXISTS ix_apis_canonical_key ON apis (canonical_key) WHERE canonical_key IS NOT NULL")
    yield


settings = get_settings()
app = FastAPI(title="ZombieShield API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(router)
