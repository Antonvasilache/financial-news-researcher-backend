from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import research, tickers

app = FastAPI(
    title="Financial News Researcher API",
    description="AI Agent backend for automated SEC filing and news analysis.",
    version="0.1.0"
)

# Allow React dev server
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

app.include_router(tickers.router)
app.include_router(research.router)

@app.get("/")
async def root():
    return {"message": "Financial News Researcher API is running"}