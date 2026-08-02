from fastapi import FastAPI

from app.routers import tickers

app = FastAPI(
    title="Financial News Researcher API",
    description="AI Agent backend for automated SEC filing and news analysis.",
    version="0.1.0"
)

app.include_router(tickers.router)

@app.get("/")
async def root():
    return {"message": "Financial News Researcher API is running"}