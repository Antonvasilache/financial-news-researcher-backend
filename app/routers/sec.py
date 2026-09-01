from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.config import Settings, get_settings
from app.schemas.sec import ParsedSecFilingResponse, SecFilingsListResponse
from app.services.sec_edgar import SecEdgarError, SecEdgarService

router = APIRouter(prefix="/api/v1/sec", tags=["SEC Filings"])


def get_sec_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> SecEdgarService:
    return SecEdgarService(settings=settings)


@router.get(
    "/filings",
    response_model=SecFilingsListResponse,
    status_code=status.HTTP_200_OK,
    summary="List recent SEC filings for a ticker",
    description="Fetches recent 10-K, 10-Q, or other filings metadata from SEC EDGAR for the given stock ticker.",
)
def list_filings(
    ticker: Annotated[str, Query(min_length=1, description="Company ticker symbol, e.g. AAPL")],
    form_type: Annotated[
        str | None,
        Query(description="Optional form filter (e.g. 10-K, 10-Q)"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=50, description="Max number of filings to return"),
    ] = 10,
    service: Annotated[SecEdgarService, Depends(get_sec_service)] = None,
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
    form_type: Annotated[
        str,
        Query(description="Form type to fetch (default 10-K, or 10-Q)"),
    ] = "10-K",
    service: Annotated[SecEdgarService, Depends(get_sec_service)] = None,
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
    form_type: Annotated[
        str | None,
        Query(description="Optional form type hint (e.g. 10-K, 10-Q)"),
    ] = None,
    service: Annotated[SecEdgarService, Depends(get_sec_service)] = None,
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
