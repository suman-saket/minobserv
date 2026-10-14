from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.database import close_db, init_db
from app.routers import alerts, ingest, query


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(title="Observability", lifespan=lifespan)
app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(alerts.router)
