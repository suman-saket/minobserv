from datetime import datetime, timedelta

from app.db.documents import AlertDocument, AlertRuleDocument
from app.models import MetricPoint
from app.store import rollup_metrics


async def evaluate_metrics(points: list[MetricPoint]) -> None:
    """Check alert rules for each service and metric in this batch.

    The compared value is the average over the rule's window, the same rollup
    the query API returns. One alert is stored per rule per window so a burst
    of points does not create a burst of alerts.
    """
    latest: dict[tuple[str, str], datetime] = {}
    for point in points:
        key = (point.service, point.metric_name)
        current = latest.get(key)
        if current is None or point.timestamp > current:
            latest[key] = point.timestamp

    for (service, metric_name), end in latest.items():
        await _evaluate_rules(service, metric_name, end)


async def _evaluate_rules(service: str, metric_name: str, end: datetime) -> None:
    rules = await AlertRuleDocument.find(
        AlertRuleDocument.service == service,
        AlertRuleDocument.metric_name == metric_name,
    ).to_list()
    for rule in rules:
        start = end - timedelta(seconds=rule.window_seconds)
        summary = await rollup_metrics(service, metric_name, start, end)
        if summary.count == 0 or summary.avg is None:
            continue
        tripped = _threshold_tripped(summary.avg, rule.comparison, rule.threshold)
        if not tripped:
            continue
        existing = await AlertDocument.find_one(
            AlertDocument.rule_id == str(rule.id),
            AlertDocument.timestamp >= start,
        )
        if existing is not None:
            continue
        await AlertDocument(
            rule_id=str(rule.id),
            service=service,
            metric_name=metric_name,
            comparison=rule.comparison,
            threshold=rule.threshold,
            value=summary.avg,
            timestamp=end,
        ).insert()


def _threshold_tripped(value: float, comparison: str, threshold: float) -> bool:
    if comparison == ">":
        return value > threshold
    return value < threshold
