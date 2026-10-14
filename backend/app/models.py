from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.time import as_utc

Level = Literal["debug", "info", "warn", "error"]
Comparison = Literal[">", "<"]


class LogEntry(BaseModel):
    timestamp: datetime
    service: str = Field(min_length=1)
    level: Level
    message: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    label: dict[str, str] = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        return as_utc(value)


class MetricPoint(BaseModel):
    timestamp: datetime
    service: str = Field(min_length=1)
    metric_name: str = Field(min_length=1)
    value: float
    tags: dict[str, str] = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        return as_utc(value)


class IngestResponse(BaseModel):
    inserted: int
    ids: list[str]


class LogResponse(BaseModel):
    id: str
    timestamp: datetime
    service: str
    level: Level
    message: str
    request_id: str
    label: dict[str, str]


class MetricResponse(BaseModel):
    id: str
    timestamp: datetime
    service: str
    metric_name: str
    value: float
    tags: dict[str, str]


class MetricRollup(BaseModel):
    count: int
    avg: float | None
    min: float | None
    max: float | None


class AlertRuleCreate(BaseModel):
    service: str = Field(min_length=1)
    metric_name: str = Field(min_length=1)
    comparison: Comparison
    threshold: float
    window_seconds: int = Field(gt=0)


class AlertRuleResponse(BaseModel):
    id: str
    service: str
    metric_name: str
    comparison: Comparison
    threshold: float
    window_seconds: int


class AlertResponse(BaseModel):
    id: str
    rule_id: str
    service: str
    metric_name: str
    comparison: Comparison
    threshold: float
    value: float
    timestamp: datetime
