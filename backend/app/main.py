from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import close_db, init_db
from app.routers import alerts, ingest, query


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(title="Observability", lifespan=lifespan)
# The Vite dev server is a different origin, so the browser can read query
# responses only when this API allows that origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET"],
    allow_headers=["Content-Type"],
)
app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(alerts.router)
