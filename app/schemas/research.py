from pydantic import BaseModel, Field


class RevenueStreamItem(BaseModel):
    name: str = Field(..., description="Name of the revenue stream or product segment")
    description: str = Field(..., description="Detailed explanation of how revenue is generated")
    revenue_type: str | None = Field(
        None, description="Classification of revenue (e.g. Product Sales, Subscription, Services)"
    )
    estimated_percentage: float | None = Field(
        None, description="Estimated percentage share of overall revenue (0-100)"
    )


class RevenueAnalysisRequest(BaseModel):
    company_name: str = Field(
        ...,
        min_length=1,
        json_schema_extra={"example": "Apple Inc."},
        description="Target company name to analyze",
    )
    model_id: str | None = Field(
        None,
        description="Optional Hugging Face model override (e.g. meta-llama/Llama-3.1-8B-Instruct)",
    )


class RevenueAnalysisResponse(BaseModel):
    company_name: str = Field(..., description="Company name analyzed")
    summary: str = Field(
        ..., description="Overview narrative of how the company generates revenue"
    )
    primary_currency: str = Field(
        "USD", description="Primary reporting currency (e.g. USD)"
    )
    revenue_streams: list[RevenueStreamItem] = Field(
        default_factory=list, description="Breakdown of key revenue streams"
    )
    model_used: str = Field(
        ..., description="Hugging Face model used to generate this analysis"
    )
