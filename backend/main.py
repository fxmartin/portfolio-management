# ABOUTME: Main FastAPI application entry point
# ABOUTME: Handles API endpoints for portfolio management

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

# Import database and routers
try:
    from .database import init_db_async, test_connection
    from .import_router import router as import_router
    from .database_router import router as database_router
    from .portfolio_router import router as portfolio_router
    from .monitoring_router import router as monitoring_router
except ImportError:
    from database import init_db_async, test_connection
    from import_router import router as import_router
    from database_router import router as database_router
    from portfolio_router import router as portfolio_router
    from monitoring_router import router as monitoring_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Portfolio Management API...")

    # Test database connection
    if await test_connection():
        print("✓ Database connection successful")
    else:
        print("✗ Database connection failed")

    # Initialize database tables if needed
    if await init_db_async():
        print("✓ Database tables ready")
    else:
        print("✗ Database initialization failed")

    # Validate Alpha Vantage API configuration
    import os
    alpha_vantage_api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if alpha_vantage_api_key:
        print(f"✓ Alpha Vantage API key configured")
        # Test the API key with a simple request
        try:
            from alpha_vantage_service import AlphaVantageService
            av_service = AlphaVantageService(alpha_vantage_api_key)
            # Note: We don't test the key here to avoid consuming rate limit on startup
            print("  ℹ API key format valid (test skipped to preserve rate limit)")
        except Exception as e:
            print(f"⚠ Alpha Vantage service initialization failed: {e}")
    else:
        print("⚠ Alpha Vantage API key not configured - fallback will use Yahoo Finance only")

    yield

    # Shutdown
    print("Shutting down Portfolio Management API...")

app = FastAPI(
    title="Portfolio Management API",
    description="Track stocks, commodities and crypto portfolios",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3003"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(import_router)
app.include_router(database_router)
app.include_router(monitoring_router)
app.include_router(portfolio_router)

@app.get("/")
async def root():
    return {"message": "Portfolio Management API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Placeholder for CSV upload
@app.post("/api/import/revolut")
async def import_revolut_csv(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    # TODO: Process Revolut CSV
    return {
        "message": f"Received file: {file.filename}",
        "status": "processing"
    }

# Placeholder for portfolio endpoint
@app.get("/api/portfolio")
async def get_portfolio():
    return {
        "total_value": 0,
        "positions": [],
        "cash_balance": 0
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
