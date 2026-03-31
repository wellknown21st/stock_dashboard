"""
Stock Data Intelligence Dashboard — Main Application

FastAPI backend serving REST APIs for stock market data analysis,
visualization, comparison, and ML-based price prediction.

Author: Mayank Mishra
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, desc
from datetime import datetime, timedelta, date
from functools import lru_cache
from typing import Optional
import pandas as pd
import numpy as np
import json

from database import init_db, get_db, StockData
from config import STOCK_SYMBOLS
from predictor import predict_prices

# ═══════════════════════════════════════════════════════════════
# App Initialization
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="Stock Data Intelligence Dashboard",
    description="""
    🚀 A comprehensive financial data platform providing:
    - Real-time stock data for 20+ major Indian companies (NSE)
    - Calculated metrics: Daily Return, Moving Averages, 52-week High/Low
    - Custom analytics: Volatility Score, Sentiment Index
    - Stock comparison and correlation analysis
    - ML-based price prediction using Linear Regression
    
    **Built with**: FastAPI, Pandas, NumPy, scikit-learn, SQLite, Chart.js
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def startup():
    """Initialize database on startup."""
    init_db()


# ═══════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════

def symbol_to_clean(symbol: str) -> str:
    """Convert user-friendly symbol to Yahoo Finance format."""
    s = symbol.upper().strip()
    if not s.endswith(".NS"):
        s += ".NS"
    return s


def get_symbol_info(symbol: str) -> dict:
    """Get company info for a symbol."""
    clean = symbol_to_clean(symbol)
    if clean in STOCK_SYMBOLS:
        return STOCK_SYMBOLS[clean]
    return {"name": symbol.upper(), "sector": "Unknown"}


# ═══════════════════════════════════════════════════════════════
# Frontend Route
# ═══════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the main dashboard page."""
    return FileResponse("static/index.html")


# ═══════════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════════

@app.get("/api/companies", tags=["Companies"])
def get_companies(db: Session = Depends(get_db)):
    """
    Returns a list of all available companies with basic info.
    
    Response includes:
    - symbol: Stock ticker
    - name: Full company name
    - sector: Industry sector
    - latest_close: Most recent closing price
    - daily_return: Latest daily return percentage
    """
    companies = db.query(
        StockData.symbol,
        StockData.company_name,
        StockData.sector,
    ).distinct().all()
    
    result = []
    for comp in companies:
        # Get latest data point
        latest = db.query(StockData).filter(
            StockData.symbol == comp.symbol
        ).order_by(desc(StockData.date)).first()
        
        clean_symbol = comp.symbol.replace(".NS", "")
        
        result.append({
            "symbol": clean_symbol,
            "full_symbol": comp.symbol,
            "name": comp.company_name,
            "sector": comp.sector,
            "latest_close": latest.close if latest else None,
            "daily_return": round(latest.daily_return * 100, 2) if latest and latest.daily_return else 0,
            "sentiment": latest.volatility_score if latest else 0,
        })
    
    # Sort by name
    result.sort(key=lambda x: x['name'])
    return {"companies": result, "count": len(result)}


@app.get("/api/data/{symbol}", tags=["Stock Data"])
def get_stock_data(
    symbol: str,
    days: int = Query(default=30, ge=1, le=365, description="Number of days of data to return"),
    db: Session = Depends(get_db)
):
    """
    Returns historical stock data for a given company.
    
    - **symbol**: Stock ticker (e.g., INFY, TCS, RELIANCE)
    - **days**: Number of days to fetch (default: 30, max: 365)
    """
    full_symbol = symbol_to_clean(symbol)
    
    cutoff_date = date.today() - timedelta(days=days)
    
    records = db.query(StockData).filter(
        StockData.symbol == full_symbol,
        StockData.date >= cutoff_date
    ).order_by(StockData.date).all()
    
    if not records:
        raise HTTPException(status_code=404, detail=f"No data found for symbol '{symbol}'")
    
    data = []
    for r in records:
        data.append({
            "date": r.date.isoformat(),
            "open": r.open,
            "high": r.high,
            "low": r.low,
            "close": r.close,
            "volume": r.volume,
            "daily_return": round(r.daily_return * 100, 2) if r.daily_return else 0,
            "ma_7": r.ma_7,
            "ma_20": r.ma_20,
            "high_52w": r.high_52w,
            "low_52w": r.low_52w,
            "volatility_score": r.volatility_score,
        })
    
    info = get_symbol_info(symbol)
    return {
        "symbol": symbol.upper(),
        "company_name": info['name'],
        "sector": info['sector'],
        "period_days": days,
        "data_points": len(data),
        "data": data
    }


@app.get("/api/summary/{symbol}", tags=["Analysis"])
def get_stock_summary(symbol: str, db: Session = Depends(get_db)):
    """
    Returns summary statistics for a stock including:
    - 52-week High and Low
    - Average closing price
    - Total volume traded
    - Average daily return
    - Volatility score
    - Current trend analysis
    """
    full_symbol = symbol_to_clean(symbol)
    
    records = db.query(StockData).filter(
        StockData.symbol == full_symbol
    ).order_by(StockData.date).all()
    
    if not records:
        raise HTTPException(status_code=404, detail=f"No data found for symbol '{symbol}'")
    
    closes = [r.close for r in records if r.close]
    highs = [r.high for r in records if r.high]
    lows = [r.low for r in records if r.low]
    volumes = [r.volume for r in records if r.volume]
    returns = [r.daily_return for r in records if r.daily_return is not None]
    
    latest = records[-1]
    earliest = records[0]
    
    # Trend analysis
    if len(closes) >= 20:
        recent_ma = np.mean(closes[-7:])
        longer_ma = np.mean(closes[-20:])
        if recent_ma > longer_ma * 1.02:
            trend = "Bullish 📈"
        elif recent_ma < longer_ma * 0.98:
            trend = "Bearish 📉"
        else:
            trend = "Sideways ➡️"
    else:
        trend = "Insufficient data"
    
    # Period return
    period_return = ((closes[-1] - closes[0]) / closes[0] * 100) if closes[0] > 0 else 0
    
    info = get_symbol_info(symbol)
    
    return {
        "symbol": symbol.upper(),
        "company_name": info['name'],
        "sector": info['sector'],
        "period": {
            "start_date": earliest.date.isoformat(),
            "end_date": latest.date.isoformat(),
            "trading_days": len(records),
        },
        "price_summary": {
            "current_close": latest.close,
            "high_52w": max(highs) if highs else None,
            "low_52w": min(lows) if lows else None,
            "avg_close": round(np.mean(closes), 2) if closes else None,
            "median_close": round(np.median(closes), 2) if closes else None,
        },
        "volume_summary": {
            "total_volume": sum(volumes),
            "avg_daily_volume": round(np.mean(volumes)) if volumes else 0,
            "max_volume_day": max(volumes) if volumes else 0,
        },
        "returns": {
            "period_return_pct": round(period_return, 2),
            "avg_daily_return_pct": round(np.mean(returns) * 100, 4) if returns else 0,
            "best_day_pct": round(max(returns) * 100, 2) if returns else 0,
            "worst_day_pct": round(min(returns) * 100, 2) if returns else 0,
        },
        "risk": {
            "volatility_score": round(latest.volatility_score, 4) if latest.volatility_score else 0,
            "std_deviation": round(np.std(closes), 2) if closes else 0,
        },
        "trend": trend,
    }


@app.get("/api/compare", tags=["Analysis"])
def compare_stocks(
    symbol1: str = Query(..., description="First stock symbol"),
    symbol2: str = Query(..., description="Second stock symbol"),
    days: int = Query(default=90, ge=7, le=365),
    db: Session = Depends(get_db)
):
    """
    Compare two stocks' performance over a given period.
    
    Returns side-by-side metrics and correlation coefficient.
    """
    full_s1 = symbol_to_clean(symbol1)
    full_s2 = symbol_to_clean(symbol2)
    
    cutoff = date.today() - timedelta(days=days)
    
    data1 = db.query(StockData).filter(
        StockData.symbol == full_s1, StockData.date >= cutoff
    ).order_by(StockData.date).all()
    
    data2 = db.query(StockData).filter(
        StockData.symbol == full_s2, StockData.date >= cutoff
    ).order_by(StockData.date).all()
    
    if not data1:
        raise HTTPException(status_code=404, detail=f"No data found for '{symbol1}'")
    if not data2:
        raise HTTPException(status_code=404, detail=f"No data found for '{symbol2}'")
    
    def summarize(records, symbol):
        closes = [r.close for r in records]
        returns = [r.daily_return for r in records if r.daily_return is not None]
        period_ret = ((closes[-1] - closes[0]) / closes[0] * 100) if closes[0] > 0 else 0
        info = get_symbol_info(symbol)
        return {
            "symbol": symbol.upper(),
            "company_name": info['name'],
            "sector": info['sector'],
            "current_close": closes[-1] if closes else None,
            "period_return_pct": round(period_ret, 2),
            "avg_daily_return_pct": round(np.mean(returns) * 100, 4) if returns else 0,
            "volatility": round(np.std(returns) * 100, 4) if returns else 0,
            "high": max(closes) if closes else None,
            "low": min(closes) if closes else None,
            "data_points": len(records),
            "closes": closes,
            "dates": [r.date.isoformat() for r in records],
        }
    
    s1 = summarize(data1, symbol1)
    s2 = summarize(data2, symbol2)
    
    # Correlation calculation
    # Align by common dates
    dates1 = {r.date: r.close for r in data1}
    dates2 = {r.date: r.close for r in data2}
    common_dates = sorted(set(dates1.keys()) & set(dates2.keys()))
    
    if len(common_dates) >= 5:
        series1 = [dates1[d] for d in common_dates]
        series2 = [dates2[d] for d in common_dates]
        correlation = round(float(np.corrcoef(series1, series2)[0, 1]), 4)
    else:
        correlation = None
    
    # Normalized price series for chart comparison
    norm1 = [round(c / s1['closes'][0] * 100, 2) for c in s1['closes']] if s1['closes'] and s1['closes'][0] > 0 else []
    norm2 = [round(c / s2['closes'][0] * 100, 2) for c in s2['closes']] if s2['closes'] and s2['closes'][0] > 0 else []
    
    # Remove raw closes from response
    s1_clean = {k: v for k, v in s1.items() if k != 'closes'}
    s2_clean = {k: v for k, v in s2.items() if k != 'closes'}
    
    return {
        "comparison_period_days": days,
        "stock1": s1_clean,
        "stock2": s2_clean,
        "correlation": correlation,
        "correlation_interpretation": (
            "Strong positive" if correlation and correlation > 0.7
            else "Moderate positive" if correlation and correlation > 0.3
            else "Weak/No correlation" if correlation and correlation > -0.3
            else "Moderate negative" if correlation and correlation > -0.7
            else "Strong negative" if correlation else "Insufficient data"
        ),
        "normalized_series": {
            "stock1": {"symbol": symbol1.upper(), "values": norm1, "dates": s1['dates']},
            "stock2": {"symbol": symbol2.upper(), "values": norm2, "dates": s2['dates']},
        },
        "winner": symbol1.upper() if (s1.get('period_return_pct', 0) or 0) >= (s2.get('period_return_pct', 0) or 0) else symbol2.upper(),
    }


@app.get("/api/gainers", tags=["Market Insights"])
def get_top_gainers(
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Returns the top gaining stocks based on latest daily return."""
    subquery = db.query(
        StockData.symbol,
        func.max(StockData.date).label('max_date')
    ).group_by(StockData.symbol).subquery()
    
    latest_records = db.query(StockData).join(
        subquery,
        (StockData.symbol == subquery.c.symbol) & (StockData.date == subquery.c.max_date)
    ).order_by(desc(StockData.daily_return)).limit(limit).all()
    
    return {
        "top_gainers": [
            {
                "symbol": r.symbol.replace(".NS", ""),
                "company_name": r.company_name,
                "close": r.close,
                "daily_return_pct": round(r.daily_return * 100, 2) if r.daily_return else 0,
                "date": r.date.isoformat(),
            }
            for r in latest_records
        ]
    }


@app.get("/api/losers", tags=["Market Insights"])
def get_top_losers(
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Returns the top losing stocks based on latest daily return."""
    subquery = db.query(
        StockData.symbol,
        func.max(StockData.date).label('max_date')
    ).group_by(StockData.symbol).subquery()
    
    latest_records = db.query(StockData).join(
        subquery,
        (StockData.symbol == subquery.c.symbol) & (StockData.date == subquery.c.max_date)
    ).order_by(StockData.daily_return).limit(limit).all()
    
    return {
        "top_losers": [
            {
                "symbol": r.symbol.replace(".NS", ""),
                "company_name": r.company_name,
                "close": r.close,
                "daily_return_pct": round(r.daily_return * 100, 2) if r.daily_return else 0,
                "date": r.date.isoformat(),
            }
            for r in latest_records
        ]
    }


@app.get("/api/volatility", tags=["Market Insights"])
def get_most_volatile(
    limit: int = Query(default=10, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Returns stocks ranked by volatility score."""
    subquery = db.query(
        StockData.symbol,
        func.max(StockData.date).label('max_date')
    ).group_by(StockData.symbol).subquery()
    
    records = db.query(StockData).join(
        subquery,
        (StockData.symbol == subquery.c.symbol) & (StockData.date == subquery.c.max_date)
    ).order_by(desc(StockData.volatility_score)).limit(limit).all()
    
    return {
        "most_volatile": [
            {
                "symbol": r.symbol.replace(".NS", ""),
                "company_name": r.company_name,
                "volatility_score": round(r.volatility_score, 4) if r.volatility_score else 0,
                "close": r.close,
                "daily_return_pct": round(r.daily_return * 100, 2) if r.daily_return else 0,
            }
            for r in records
        ]
    }


@app.get("/api/sectors", tags=["Market Insights"])
def get_sector_performance(db: Session = Depends(get_db)):
    """Returns average performance grouped by sector."""
    subquery = db.query(
        StockData.symbol,
        func.max(StockData.date).label('max_date')
    ).group_by(StockData.symbol).subquery()
    
    latest = db.query(StockData).join(
        subquery,
        (StockData.symbol == subquery.c.symbol) & (StockData.date == subquery.c.max_date)
    ).all()
    
    sectors = {}
    for r in latest:
        if r.sector not in sectors:
            sectors[r.sector] = {"returns": [], "volatilities": [], "companies": []}
        sectors[r.sector]["returns"].append(r.daily_return or 0)
        sectors[r.sector]["volatilities"].append(r.volatility_score or 0)
        sectors[r.sector]["companies"].append(r.symbol.replace(".NS", ""))
    
    result = []
    for sector, data in sectors.items():
        result.append({
            "sector": sector,
            "avg_daily_return_pct": round(np.mean(data["returns"]) * 100, 4),
            "avg_volatility": round(np.mean(data["volatilities"]), 4),
            "num_companies": len(data["companies"]),
            "companies": data["companies"],
        })
    
    result.sort(key=lambda x: x['avg_daily_return_pct'], reverse=True)
    return {"sectors": result}


@app.get("/api/predict/{symbol}", tags=["AI Prediction"])
def predict_stock(
    symbol: str,
    days: int = Query(default=7, ge=1, le=30, description="Number of days to predict"),
    db: Session = Depends(get_db)
):
    """
    Predict future stock prices using Linear Regression ML model.
    
    ⚠️ Disclaimer: This is a simplified model for educational purposes only.
    """
    full_symbol = symbol_to_clean(symbol)
    
    records = db.query(StockData).filter(
        StockData.symbol == full_symbol
    ).order_by(StockData.date).all()
    
    if not records:
        raise HTTPException(status_code=404, detail=f"No data found for '{symbol}'")
    
    # Convert to DataFrame for the predictor
    df = pd.DataFrame([{
        'date': r.date,
        'open': r.open,
        'high': r.high,
        'low': r.low,
        'close': r.close,
        'volume': r.volume,
        'daily_return': r.daily_return,
        'ma_7': r.ma_7,
        'ma_20': r.ma_20,
    } for r in records])
    
    info = get_symbol_info(symbol)
    result = predict_prices(df, days)
    result['symbol'] = symbol.upper()
    result['company_name'] = info['name']
    
    return result


@app.get("/api/correlation", tags=["Analysis"])
def get_correlation_matrix(db: Session = Depends(get_db)):
    """
    Returns a correlation matrix of closing prices for all stocks.
    Custom metric showing how stocks move relative to each other.
    """
    symbols = db.query(distinct(StockData.symbol)).all()
    symbols = [s[0] for s in symbols]
    
    # Get last 90 days of data for each symbol
    cutoff = date.today() - timedelta(days=90)
    
    price_data = {}
    for sym in symbols:
        records = db.query(StockData.date, StockData.close).filter(
            StockData.symbol == sym,
            StockData.date >= cutoff
        ).order_by(StockData.date).all()
        
        price_data[sym.replace(".NS", "")] = {r.date: r.close for r in records}
    
    # Find common dates
    all_dates = set()
    for sym_data in price_data.values():
        all_dates.update(sym_data.keys())
    common_dates = sorted(all_dates)
    
    # Build DataFrame
    df_dict = {}
    for sym, data in price_data.items():
        df_dict[sym] = [data.get(d) for d in common_dates]
    
    df = pd.DataFrame(df_dict, index=common_dates)
    df = df.dropna(axis=1, how='all').dropna()
    
    if df.empty or len(df.columns) < 2:
        return {"error": "Insufficient data for correlation matrix"}
    
    corr = df.corr().round(4)
    
    matrix = {}
    for col in corr.columns:
        matrix[col] = {row: corr.at[row, col] for row in corr.index}
    
    return {
        "symbols": list(corr.columns),
        "matrix": matrix,
        "period_days": 90,
    }


@app.get("/api/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """Check API health and data status."""
    total_records = db.query(func.count(StockData.id)).scalar()
    total_symbols = db.query(func.count(distinct(StockData.symbol))).scalar()
    latest_date = db.query(func.max(StockData.date)).scalar()
    
    return {
        "status": "healthy",
        "total_records": total_records,
        "total_symbols": total_symbols,
        "latest_data_date": latest_date.isoformat() if latest_date else None,
        "api_version": "1.0.0",
    }


# ═══════════════════════════════════════════════════════════════
# Run with: uvicorn main:app --reload
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
