from datetime import datetime
from typing import Literal

from beanie import Document
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

Comparison = Literal[">", "<"]


class LogDocument(Document):
    timestamp: datetime
    service: str
    level: str
    message: str
    request_id: str
    label: dict[str, str] = Field(default_factory=dict)

    class Settings:
        name = "logs"
        indexes = [
            IndexModel([("service", ASCENDING), ("timestamp", DESCENDING)]),
        ]


class MetricDocument(Document):
    timestamp: datetime
    service: str
    metric_name: str
    value: float
    tags: dict[str, str] = Field(default_factory=dict)

    class Settings:
        name = "metrics"
        indexes = [
            IndexModel([("service", ASCENDING), ("timestamp", DESCENDING)]),
            IndexModel([("metric_name", ASCENDING), ("timestamp", DESCENDING)]),
        ]


class AlertRuleDocument(Document):
    service: str
    metric_name: str
    comparison: Comparison
    threshold: float
    window_seconds: int

    class Settings:
        name = "alert_rules"
        indexes = [
            IndexModel([("service", ASCENDING), ("metric_name", ASCENDING)]),
        ]


class AlertDocument(Document):
    rule_id: str
    service: str
    metric_name: str
    comparison: Comparison
    threshold: float
    value: float
    timestamp: datetime

    class Settings:
        name = "alerts"
        indexes = [
            IndexModel([("rule_id", ASCENDING), ("timestamp", DESCENDING)]),
            IndexModel([("service", ASCENDING), ("timestamp", DESCENDING)]),
        ]
