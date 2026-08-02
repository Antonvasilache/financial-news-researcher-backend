from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from app.schemas.ticker import TickerCreate, TickerResponse

router = APIRouter(
    prefix="/tickers",
    tags=["Tickers"]
)

# In-memory database mock
ticker_db: dict[int, dict] = {
    1: {
        "id": 1,
        "symbol": "AMD",
        "company_name": "Advanced Micro Devices, Inc.",
        "is_active": True,
        "created_at": datetime.now(UTC)
    }
}
id_counter = 2

@router.get("/", response_model=list[TickerResponse])
async def get_all_tickers():
    """Retrieve all tracked tickers."""
    return list(ticker_db.values())

@router.get("/{ticker_id}", response_model=TickerResponse)
async def get_ticker(ticker_id: int):
    """Retrieve a single ticker by ID."""
    if ticker_id not in ticker_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticker with ID {ticker_id} not found"
        )

    return ticker_db[ticker_id]

@router.post("/", response_model=TickerResponse, status_code=status.HTTP_201_CREATED)
async def create_ticker(payload: TickerCreate):
    """Add new ticker to track."""
    global id_counter

    for existing in ticker_db.values():
        if existing["symbol"].upper() == payload.symbol.upper():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ticker {payload.symbol} is already registered"
            )

    new_ticker = {
        "id": id_counter,
        "symbol": payload.symbol.upper(),
        "company_name": payload.company_name,
        "is_active": True,
        "created_at": datetime.now(UTC)
    }
    ticker_db[id_counter] = new_ticker
    id_counter += 1

    return new_ticker

@router.delete("/{ticker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticker(ticker_id: int):
    """Remove a ticker from tracking."""
    if ticker_id not in ticker_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticker with ID {ticker_id} not found"
        )

    del ticker_db[ticker_id]
