from datetime import datetime

from pymongo import DESCENDING

from app.db.documents import (
    AlertDocument,
    AlertRuleDocument,
    LogDocument,
    MetricDocument,
)
from app.models import (
    AlertResponse,
    AlertRuleCreate,
    AlertRuleResponse,
    IngestResponse,
    LogEntry,
    LogResponse,
    MetricPoint,
    MetricResponse,
    MetricRollup,
)
from app.time import as_utc


async def insert_logs(entries: list[LogEntry]) -> IngestResponse:
    if not entries:
        return IngestResponse(inserted=0, ids=[])
    docs = [LogDocument(**entry.model_dump()) for entry in entries]
    result = await LogDocument.insert_many(docs)
    return IngestResponse(
        inserted=len(result.inserted_ids),
        ids=[str(item) for item in result.inserted_ids],
    )


async def insert_metrics(points: list[MetricPoint]) -> IngestResponse:
    if not points:
        return IngestResponse(inserted=0, ids=[])
    docs = [MetricDocument(**point.model_dump()) for point in points]
    result = await MetricDocument.insert_many(docs)
    return IngestResponse(
        inserted=len(result.inserted_ids),
        ids=[str(item) for item in result.inserted_ids],
    )


async def query_logs(
    service: str | None,
    level: str | None,
    from_time: datetime | None,
    to_time: datetime | None,
    limit: int,
) -> list[LogResponse]:
    filters = _range_filters(LogDocument, service, from_time, to_time)
    if level:
        filters.append(LogDocument.level == level)
    docs = await _newest(LogDocument, filters, limit)
    return [_log_response(doc) for doc in docs]


async def query_metrics(
    service: str | None,
    name: str | None,
    from_time: datetime | None,
    to_time: datetime | None,
    limit: int,
) -> list[MetricResponse]:
    filters = _metric_filters(service, name, from_time, to_time)
    docs = await _newest(MetricDocument, filters, limit)
    return [_metric_response(doc) for doc in docs]


async def rollup_metrics(
    service: str | None,
    name: str | None,
    from_time: datetime | None,
    to_time: datetime | None,
) -> MetricRollup:
    """Aggregate metric values with count, avg, min, and max.

    Alert checks use this same rollup, so a rule and a query see one number
    for the window instead of two different calculations.
    """
    match: dict = {}
    if service:
        match["service"] = service
    if name:
        match["metric_name"] = name
    timestamp_filter = _timestamp_match(from_time, to_time)
    if timestamp_filter:
        match["timestamp"] = timestamp_filter

    rows = await MetricDocument.aggregate(
        [
            {"$match": match},
            {
                "$group": {
                    "_id": None,
                    "count": {"$sum": 1},
                    "avg": {"$avg": "$value"},
                    "min": {"$min": "$value"},
                    "max": {"$max": "$value"},
                }
            },
        ]
    ).to_list()
    if not rows:
        return MetricRollup(count=0, avg=None, min=None, max=None)
    row = rows[0]
    return MetricRollup(
        count=row["count"],
        avg=row["avg"],
        min=row["min"],
        max=row["max"],
    )


async def insert_rule(rule: AlertRuleCreate) -> AlertRuleResponse:
    doc = AlertRuleDocument(**rule.model_dump())
    await doc.insert()
    return _rule_response(doc)


async def list_rules() -> list[AlertRuleResponse]:
    docs = await AlertRuleDocument.find().to_list()
    return [_rule_response(doc) for doc in docs]


async def list_alerts(service: str | None, limit: int) -> list[AlertResponse]:
    filters = []
    if service:
        filters.append(AlertDocument.service == service)
    docs = await _newest(AlertDocument, filters, limit)
    return [_alert_response(doc) for doc in docs]


def _range_filters(document, service: str | None, from_time: datetime | None, to_time: datetime | None) -> list:
    filters = []
    if service:
        filters.append(document.service == service)
    start, end = _bounds(from_time, to_time)
    if start is not None:
        filters.append(document.timestamp >= start)
    if end is not None:
        filters.append(document.timestamp <= end)
    return filters


def _metric_filters(
    service: str | None,
    name: str | None,
    from_time: datetime | None,
    to_time: datetime | None,
) -> list:
    filters = _range_filters(MetricDocument, service, from_time, to_time)
    if name:
        filters.append(MetricDocument.metric_name == name)
    return filters


def _bounds(
    from_time: datetime | None,
    to_time: datetime | None,
) -> tuple[datetime | None, datetime | None]:
    start = as_utc(from_time) if from_time is not None else None
    end = as_utc(to_time) if to_time is not None else None
    return start, end


def _timestamp_match(from_time: datetime | None, to_time: datetime | None) -> dict:
    start, end = _bounds(from_time, to_time)
    match: dict = {}
    if start is not None:
        match["$gte"] = start
    if end is not None:
        match["$lte"] = end
    return match


async def _newest(document, filters: list, limit: int) -> list:
    query = document.find(*filters)
    return await query.sort([("timestamp", DESCENDING)]).limit(limit).to_list()


def _log_response(doc: LogDocument) -> LogResponse:
    return LogResponse(
        id=str(doc.id),
        timestamp=doc.timestamp,
        service=doc.service,
        level=doc.level,
        message=doc.message,
        request_id=doc.request_id,
        label=doc.label,
    )


def _metric_response(doc: MetricDocument) -> MetricResponse:
    return MetricResponse(
        id=str(doc.id),
        timestamp=doc.timestamp,
        service=doc.service,
        metric_name=doc.metric_name,
        value=doc.value,
        tags=doc.tags,
    )


def _rule_response(doc: AlertRuleDocument) -> AlertRuleResponse:
    return AlertRuleResponse(
        id=str(doc.id),
        service=doc.service,
        metric_name=doc.metric_name,
        comparison=doc.comparison,
        threshold=doc.threshold,
        window_seconds=doc.window_seconds,
    )


def _alert_response(doc: AlertDocument) -> AlertResponse:
    return AlertResponse(
        id=str(doc.id),
        rule_id=doc.rule_id,
        service=doc.service,
        metric_name=doc.metric_name,
        comparison=doc.comparison,
        threshold=doc.threshold,
        value=doc.value,
        timestamp=doc.timestamp,
    )
