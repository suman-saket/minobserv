from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.config import settings
from app.db.documents import (
    AlertDocument,
    AlertRuleDocument,
    LogDocument,
    MetricDocument,
)

client: AsyncMongoClient | None = None


async def init_db() -> None:
    """Open Mongo and register the Beanie models for this process."""
    global client
    client = AsyncMongoClient(settings.MONGODB_URL)
    await init_beanie_models(client)


async def init_beanie_models(mongo: AsyncMongoClient) -> None:
    await init_beanie(
        database=mongo[settings.MONGODB_DB],
        document_models=[
            LogDocument,
            MetricDocument,
            AlertRuleDocument,
            AlertDocument,
        ],
    )


async def close_db() -> None:
    global client
    if client is not None:
        await client.close()
        client = None
