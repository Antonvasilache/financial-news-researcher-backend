from fastapi import APIRouter, status

from app.routers.sec import analyze_company_financials
from app.schemas.ml import CompanyFinancialAnalysisResponse

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics & ML"])

# Reuses the unified analyze_company_financials function declaration for the query-parameter endpoint
router.add_api_route(
    "/trends-and-anomalies",
    analyze_company_financials,
    methods=["GET"],
    response_model=CompanyFinancialAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze corporate financial trends and detect accounting anomalies",
    description="Evaluates SEC XBRL financial facts using scikit-learn Isolation Forest and trend classification to flag anomalies and identify growth regimes.",
)
