from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import SettingsDep
from app.schemas.research import RevenueAnalysisRequest, RevenueAnalysisResponse
from app.services.revenue_researcher import (
    RevenueResearchError,
    RevenueResearcherService,
)

router = APIRouter(prefix="/api/v1/research", tags=["Research"])


def get_revenue_service(
    settings: SettingsDep,
) -> RevenueResearcherService:
    return RevenueResearcherService(settings=settings)


RevenueServiceDep = Annotated[RevenueResearcherService, Depends(get_revenue_service)]


@router.post(
    "/revenue-streams",
    response_model=RevenueAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze company revenue streams",
    description="Queries Hugging Face LLM Inference API to return structured key revenue streams for a given company.",
)
def analyze_revenue_streams(
    payload: RevenueAnalysisRequest,
    service: RevenueServiceDep,
) -> RevenueAnalysisResponse:
    """Analyze company revenue streams using Hugging Face LLM Inference API."""
    try:
        return service.analyze_revenue_streams(
            company_name=payload.company_name, model_id=payload.model_id
        )
    except RevenueResearchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
