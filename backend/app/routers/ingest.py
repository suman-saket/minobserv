from fastapi import APIRouter

from app.alerts.evaluate import evaluate_metrics
from app.models import IngestResponse, LogEntry, MetricPoint
from app.store import insert_logs, insert_metrics

router = APIRouter(prefix="/v1/ingest", tags=["ingest"])


@router.post("/logs", response_model=IngestResponse)
async def ingest_logs(entries: list[LogEntry]) -> IngestResponse:
    return await insert_logs(entries)


@router.post("/metrics", response_model=IngestResponse)
async def ingest_metrics(points: list[MetricPoint]) -> IngestResponse:
    result = await insert_metrics(points)
    await evaluate_metrics(points)
    return result
