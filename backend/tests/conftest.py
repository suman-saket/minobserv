import os

os.environ["MONGODB_DB"] = "observability_test"

from pymongo import MongoClient
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


@pytest.fixture
def client():
    mongo = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=2000)
    mongo.admin.command("ping")
    mongo.drop_database(settings.MONGODB_DB)
    with TestClient(app) as test_client:
        yield test_client
    mongo.drop_database(settings.MONGODB_DB)
    mongo.close()
