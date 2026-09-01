from pydantic import BaseModel, Field


class SecFilingMetadata(BaseModel):
    accession_number: str = Field(..., description="SEC EDGAR unique accession number")
    form_type: str = Field(..., description="Form type (e.g. 10-K, 10-Q)")
    filing_date: str = Field(..., description="Filing submission date (YYYY-MM-DD)")
    report_date: str | None = Field(
        None, description="Period end date for the report (YYYY-MM-DD)"
    )
    primary_document: str = Field(..., description="Primary document file name")
    document_url: str = Field(..., description="Direct URL to view document on SEC EDGAR")
    description: str | None = Field(None, description="Filing document description")


class SecFilingsListResponse(BaseModel):
    ticker: str = Field(..., description="Company stock ticker symbol (e.g. AAPL)")
    cik: str = Field(..., description="10-digit Central Index Key identifier")
    company_name: str = Field(..., description="Company legal name registered with SEC")
    filings: list[SecFilingMetadata] = Field(
        default_factory=list, description="List of matching SEC filings"
    )
    total_count: int = Field(..., description="Total number of filings returned")


class FilingSection(BaseModel):
    item_id: str = Field(
        ..., description="Standardized item key (e.g. item_1, item_1a, item_7)"
    )
    title: str = Field(..., description="Section title or heading")
    content: str = Field(..., description="Clean text content extracted for this section")
    character_count: int = Field(
        ..., description="Total character length of the section content"
    )


class ParsedSecFilingResponse(BaseModel):
    ticker: str = Field(..., description="Company stock ticker symbol")
    cik: str = Field(..., description="10-digit Central Index Key identifier")
    company_name: str = Field(..., description="Company legal name")
    form_type: str = Field(..., description="Form type (10-K or 10-Q)")
    accession_number: str = Field(..., description="SEC EDGAR accession number")
    filing_date: str = Field(..., description="Filing date")
    report_date: str | None = Field(None, description="Report period end date")
    sections: dict[str, FilingSection] = Field(
        default_factory=dict,
        description="Extracted key sections keyed by item_id (e.g. item_1a, item_7)",
    )
    raw_text_preview: str = Field(
        ..., description="Initial excerpt/preview of clean filing text"
    )
