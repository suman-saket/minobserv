from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Query

from app.models import LogResponse, MetricResponse, MetricRollup
from app.store import query_logs, query_metrics, rollup_metrics

router = APIRouter(prefix="/v1/query", tags=["query"])

Level = Literal["debug", "info", "warn", "error"]


@router.get("/logs", response_model=list[LogResponse])
async def get_logs(
    service: str | None = None,
    level: Level | None = None,
    from_time: datetime | None = Query(default=None, alias="from"),
    to_time: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[LogResponse]:
    return await query_logs(service, level, from_time, to_time, limit)


@router.get("/metrics/rollup", response_model=MetricRollup)
async def get_metric_rollup(
    service: str | None = None,
    name: str | None = None,
    from_time: datetime | None = Query(default=None, alias="from"),
    to_time: datetime | None = Query(default=None, alias="to"),
) -> MetricRollup:
    return await rollup_metrics(service, name, from_time, to_time)


@router.get("/metrics", response_model=list[MetricResponse])
async def get_metrics(
    service: str | None = None,
    name: str | None = None,
    from_time: datetime | None = Query(default=None, alias="from"),
    to_time: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[MetricResponse]:
    return await query_metrics(service, name, from_time, to_time, limit)
