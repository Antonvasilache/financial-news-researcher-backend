from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.core.config import Settings, get_settings
from app.schemas.financials import CompanyFinancialsResponse
from app.schemas.sec import ParsedSecFilingResponse, SecFilingsListResponse
from app.services.financial_metrics import FinancialMetricsService
from app.services.sec_edgar import SecEdgarError, SecEdgarService

router = APIRouter(prefix="/api/v1/sec", tags=["SEC Filings"])


def get_sec_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> SecEdgarService:
    return SecEdgarService(settings=settings)


def get_financial_metrics_service() -> FinancialMetricsService:
    return FinancialMetricsService()


SecServiceDep = Annotated[SecEdgarService, Depends(get_sec_service)]
MetricsServiceDep = Annotated[FinancialMetricsService, Depends(get_financial_metrics_service)]


@router.get(
    "/filings",
    response_model=SecFilingsListResponse,
    status_code=status.HTTP_200_OK,
    summary="List recent SEC filings for a ticker",
    description="Fetches recent 10-K, 10-Q, or other filings metadata from SEC EDGAR for the given stock ticker.",
)
def list_filings(
    ticker: Annotated[str, Query(min_length=1, description="Company ticker symbol, e.g. AAPL")],
    service: SecServiceDep,
    form_type: Annotated[
        str | None,
        Query(description="Optional form filter (e.g. 10-K, 10-Q)"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=50, description="Max number of filings to return"),
    ] = 10,
) -> SecFilingsListResponse:
    """Retrieve list of recent filings metadata for a ticker."""
    try:
        form_types = [form_type] if form_type else None
        return service.get_company_filings(
            ticker=ticker, form_types=form_types, limit=limit
        )
    except SecEdgarError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/filings/{ticker}/latest",
    response_model=ParsedSecFilingResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch and parse latest 10-K or 10-Q filing",
    description="Retrieves the most recent 10-K or 10-Q filing for a ticker and extracts structured sections.",
)
def get_latest_filing(
    ticker: str,
    service: SecServiceDep,
    form_type: Annotated[
        str,
        Query(description="Form type to fetch (default 10-K, or 10-Q)"),
    ] = "10-K",
) -> ParsedSecFilingResponse:
    """Fetch and parse the latest filing (10-K or 10-Q) for a company."""
    try:
        filings_data = service.get_company_filings(
            ticker=ticker, form_types=[form_type], limit=1
        )
        if not filings_data.filings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No {form_type} filings found for ticker '{ticker.upper()}'.",
            )
        latest_filing = filings_data.filings[0]
        return service.fetch_and_parse_filing(
            ticker=ticker,
            accession_number=latest_filing.accession_number,
            form_type=latest_filing.form_type,
        )
    except SecEdgarError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/filings/{ticker}/{accession_number}",
    response_model=ParsedSecFilingResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch and parse specific filing by accession number",
    description="Downloads and parses key sections (Risk Factors, MD&A, Business) for a given filing accession number.",
)
def get_filing_by_accession(
    ticker: str,
    accession_number: str,
    service: SecServiceDep,
    form_type: Annotated[
        str | None,
        Query(description="Optional form type hint (e.g. 10-K, 10-Q)"),
    ] = None,
) -> ParsedSecFilingResponse:
    """Fetch and parse a specific filing by accession number."""
    try:
        return service.fetch_and_parse_filing(
            ticker=ticker,
            accession_number=accession_number,
            form_type=form_type,
        )
    except SecEdgarError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/financials/{ticker}",
    response_model=CompanyFinancialsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get quantitative financial statements and calculated ratios for a company",
    description="Fetches US-GAAP facts from SEC EDGAR XBRL and calculates key financial metrics and ratios (margins, liquidity, solvency, YoY growth).",
)
def get_company_financials(
    ticker: Annotated[
        str,
        Path(
            min_length=1,
            max_length=10,
            pattern=r"^[A-Za-z0-9.-]+$",
            description="Company ticker symbol, e.g. AAPL",
        ),
    ],
    sec_service: SecServiceDep,
    metrics_service: MetricsServiceDep,
    annual_limit: Annotated[
        int,
        Query(ge=1, le=20, description="Max annual periods (10-K) to return"),
    ] = 5,
    quarterly_limit: Annotated[
        int,
        Query(ge=1, le=30, description="Max quarterly periods (10-Q) to return"),
    ] = 8,
) -> CompanyFinancialsResponse:
    """Fetch SEC XBRL company facts and return structured financials and calculated ratios."""
    try:
        cik, company_name = sec_service.get_cik_by_ticker(ticker)
        facts_data = sec_service.get_company_facts(ticker=ticker, cik=cik)
        return metrics_service.extract_company_financials(
            facts_data=facts_data,
            ticker=ticker,
            cik=cik,
            company_name=company_name,
            annual_limit=annual_limit,
            quarterly_limit=quarterly_limit,
        )
    except SecEdgarError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

