from fastapi import APIRouter, Query

from app.models import AlertResponse, AlertRuleCreate, AlertRuleResponse
from app.store import insert_rule, list_alerts, list_rules

router = APIRouter(prefix="/v1/alerts", tags=["alerts"])


@router.post("/rules", response_model=AlertRuleResponse)
async def create_rule(rule: AlertRuleCreate) -> AlertRuleResponse:
    return await insert_rule(rule)


@router.get("/rules", response_model=list[AlertRuleResponse])
async def get_rules() -> list[AlertRuleResponse]:
    return await list_rules()


@router.get("", response_model=list[AlertResponse])
async def get_alerts(
    service: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[AlertResponse]:
    return await list_alerts(service, limit)
