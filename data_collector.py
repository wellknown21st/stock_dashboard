"""
Data Collection & Preparation Module.

Fetches stock market data using yfinance, cleans it with Pandas,
and calculates derived metrics including:
- Daily Return
- 7-day and 20-day Moving Averages
- 52-week High/Low
- Volatility Score
- Mock Sentiment Index

Falls back to realistic synthetic data generation if yfinance is unavailable.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
import time

from config import STOCK_SYMBOLS, DATA_PERIOD, DATA_INTERVAL
from database import StockData, init_db, SessionLocal


# ═══════════════════════════════════════════════════════════════
# Realistic base prices for Indian NSE stocks (approximate)
# ═══════════════════════════════════════════════════════════════

BASE_PRICES = {
    "RELIANCE.NS": 1250.0,
    "TCS.NS": 3800.0,
    "INFY.NS": 1550.0,
    "HDFCBANK.NS": 1680.0,
    "ICICIBANK.NS": 1220.0,
    "HINDUNILVR.NS": 2350.0,
    "ITC.NS": 430.0,
    "SBIN.NS": 780.0,
    "BHARTIARTL.NS": 1680.0,
    "KOTAKBANK.NS": 1750.0,
    "LT.NS": 3400.0,
    "WIPRO.NS": 480.0,
    "HCLTECH.NS": 1580.0,
    "TATAMOTORS.NS": 720.0,
    "MARUTI.NS": 12500.0,
    "SUNPHARMA.NS": 1780.0,
    "TITAN.NS": 3250.0,
    "ADANIENT.NS": 2200.0,
    "POWERGRID.NS": 310.0,
    "NTPC.NS": 340.0,
}

# Volatility profiles per sector
SECTOR_VOLATILITY = {
    "Energy": 0.018,
    "IT": 0.016,
    "Banking": 0.015,
    "FMCG": 0.012,
    "Telecom": 0.014,
    "Infrastructure": 0.017,
    "Automobile": 0.020,
    "Pharma": 0.016,
    "Consumer": 0.015,
    "Conglomerate": 0.025,
    "Utilities": 0.013,
}


def generate_synthetic_stock_data(symbol: str, info: dict, num_days: int = 252) -> pd.DataFrame:
    """
    Generate realistic synthetic stock data using Geometric Brownian Motion (GBM).
    
    This produces data that closely mimics real stock behavior with:
    - Realistic price movements with momentum and mean reversion
    - Volume patterns (higher volume on big price move days)
    - Weekend gaps excluded
    - Sector-appropriate volatility
    
    Args:
        symbol: Stock ticker
        info: Company info dict with 'name' and 'sector'
        num_days: Number of trading days to generate
    
    Returns:
        DataFrame with OHLCV data
    """
    np.random.seed(hash(symbol) % (2**31))
    
    base_price = BASE_PRICES.get(symbol, 1000.0)
    volatility = SECTOR_VOLATILITY.get(info['sector'], 0.016)
    
    # Drift (slight upward bias for Indian markets)
    drift = 0.0003  # ~7.5% annual return
    
    # Generate trading days (exclude weekends)
    end_date = date.today() - timedelta(days=1)
    dates = []
    current = end_date - timedelta(days=int(num_days * 1.5))
    while len(dates) < num_days:
        if current.weekday() < 5:  # Monday to Friday
            dates.append(current)
        current += timedelta(days=1)
    
    # Generate price path using GBM
    closes = [base_price]
    for i in range(1, num_days):
        # Add some autocorrelation for realistic momentum
        random_return = np.random.normal(drift, volatility)
        # Mean reversion component
        if closes[-1] > base_price * 1.3:
            random_return -= 0.003
        elif closes[-1] < base_price * 0.7:
            random_return += 0.003
        
        new_price = closes[-1] * (1 + random_return)
        closes.append(round(new_price, 2))
    
    # Generate OHLV from close prices
    data = []
    base_volume = int(base_price * 5000)  # Volume proportional to price
    
    for i in range(num_days):
        close = closes[i]
        
        # Intraday range (typically 1-3% of close)
        intraday_range = close * np.random.uniform(0.005, 0.025)
        
        # Open near previous close with small gap
        if i > 0:
            gap = np.random.normal(0, close * 0.003)
            open_price = round(closes[i-1] + gap, 2)
        else:
            open_price = round(close * (1 + np.random.uniform(-0.005, 0.005)), 2)
        
        # High and Low
        if close > open_price:  # Bullish day
            high = round(max(close, open_price) + np.random.uniform(0, intraday_range * 0.4), 2)
            low = round(min(close, open_price) - np.random.uniform(0, intraday_range * 0.3), 2)
        else:  # Bearish day
            high = round(max(close, open_price) + np.random.uniform(0, intraday_range * 0.3), 2)
            low = round(min(close, open_price) - np.random.uniform(0, intraday_range * 0.4), 2)
        
        # Volume (higher on big move days)
        daily_change = abs(close - open_price) / open_price if open_price > 0 else 0
        volume_multiplier = 1.0 + daily_change * 20  # Big moves = more volume
        volume = int(base_volume * np.random.uniform(0.5, 1.5) * volume_multiplier)
        
        data.append({
            'date': dates[i],
            'open': max(open_price, 1),
            'high': max(high, max(open_price, close)),
            'low': min(low, min(open_price, close)),
            'close': max(close, 1),
            'volume': volume,
        })
    
    df = pd.DataFrame(data)
    return df


def fetch_stock_data(symbol: str, period: str = DATA_PERIOD, interval: str = DATA_INTERVAL) -> pd.DataFrame:
    """
    Fetch stock data from Yahoo Finance using yfinance.
    Falls back to synthetic data if yfinance fails or returns empty data.
    """
    print(f"  📥 Fetching data for {symbol}...")
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if not df.empty:
            # Reset index to make Date a column
            df = df.reset_index()
            
            # Rename columns to standardized format
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]
            
            # Keep only relevant columns
            relevant_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            df = df[[col for col in relevant_cols if col in df.columns]]
            
            print(f"  ✅ Fetched {len(df)} rows from Yahoo Finance")
            return df
        
        print(f"  ⚠️  No data from yfinance for {symbol}, using synthetic data")
    except Exception as e:
        print(f"  ⚠️  yfinance error for {symbol}: {e}")
    
    # Fallback: generate synthetic data
    return None  # Signal to use synthetic data


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and preprocess the stock data.
    
    Handles:
    - Missing values (forward fill, then backward fill)
    - Incorrect date formats
    - Negative/zero prices
    - Duplicate entries
    """
    if df.empty:
        return df
    
    # Ensure date column is datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Remove timezone info if present
    if df['date'].dt.tz is not None:
        df['date'] = df['date'].dt.tz_localize(None)
    
    # Convert date to date only (no time component)
    df['date'] = df['date'].dt.date
    
    # Remove duplicates based on date
    df = df.drop_duplicates(subset=['date'], keep='last')
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    # Handle missing values - forward fill then backward fill
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    df[numeric_cols] = df[numeric_cols].ffill().bfill()
    
    # Remove rows with zero or negative prices
    for col in ['open', 'high', 'low', 'close']:
        df = df[df[col] > 0]
    
    # Ensure volume is non-negative
    df['volume'] = df['volume'].clip(lower=0)
    
    # Round price columns to 2 decimal places
    for col in ['open', 'high', 'low', 'close']:
        df[col] = df[col].round(2)
    
    return df.reset_index(drop=True)


def calculate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate derived financial metrics.
    
    Metrics:
    - Daily Return: (Close - Open) / Open
    - 7-day Moving Average of Close
    - 20-day Moving Average of Close
    - 52-week High (rolling max of High over 252 trading days)
    - 52-week Low (rolling min of Low over 252 trading days)
    - Volatility Score: Rolling std of daily returns (20-day window)
    """
    if df.empty:
        return df
    
    # Daily Return = (Close - Open) / Open
    df['daily_return'] = ((df['close'] - df['open']) / df['open']).round(6)
    
    # 7-day Moving Average
    df['ma_7'] = df['close'].rolling(window=7, min_periods=1).mean().round(2)
    
    # 20-day Moving Average
    df['ma_20'] = df['close'].rolling(window=20, min_periods=1).mean().round(2)
    
    # 52-week High (252 trading days ≈ 1 year)
    df['high_52w'] = df['high'].rolling(window=252, min_periods=1).max().round(2)
    
    # 52-week Low
    df['low_52w'] = df['low'].rolling(window=252, min_periods=1).min().round(2)
    
    # Volatility Score: Rolling standard deviation of daily returns (20-day)
    df['volatility_score'] = df['daily_return'].rolling(window=20, min_periods=5).std().round(6)
    
    # Fill any remaining NaN in metric columns
    df['volatility_score'] = df['volatility_score'].fillna(0)
    
    return df


def generate_sentiment_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate a mock Sentiment Index based on price action and volume patterns.
    
    The sentiment score ranges from -1.0 (very bearish) to 1.0 (very bullish).
    It's calculated using:
    - Price momentum (close vs moving averages)
    - Volume trend
    - Daily return direction
    """
    if df.empty:
        return df
    
    sentiment = np.zeros(len(df))
    
    for i in range(len(df)):
        score = 0.0
        
        # Price above 7-day MA → bullish signal (+0.3)
        if df.iloc[i]['close'] > df.iloc[i]['ma_7']:
            score += 0.3
        else:
            score -= 0.3
        
        # Price above 20-day MA → bullish signal (+0.3)
        if df.iloc[i]['close'] > df.iloc[i]['ma_20']:
            score += 0.3
        else:
            score -= 0.3
        
        # Positive daily return → bullish (+0.2)
        if df.iloc[i]['daily_return'] > 0:
            score += 0.2
        else:
            score -= 0.2
        
        # Volume spike detection (above average) → bullish confirmation (+0.2)
        avg_vol = df['volume'].iloc[max(0, i-20):i+1].mean()
        if avg_vol > 0 and df.iloc[i]['volume'] > avg_vol * 1.2:
            score += 0.2 if df.iloc[i]['daily_return'] > 0 else -0.2
        
        sentiment[i] = np.clip(score, -1.0, 1.0)
    
    df['sentiment_index'] = np.round(sentiment, 2)
    return df


def store_data(db: Session, symbol: str, company_info: dict, df: pd.DataFrame):
    """Store processed stock data into the database."""
    if df.empty:
        return
    
    # Delete existing data for this symbol to avoid duplicates
    db.query(StockData).filter(StockData.symbol == symbol).delete()
    
    records = []
    for _, row in df.iterrows():
        record = StockData(
            symbol=symbol,
            company_name=company_info['name'],
            sector=company_info['sector'],
            date=row['date'],
            open=row['open'],
            high=row['high'],
            low=row['low'],
            close=row['close'],
            volume=int(row['volume']) if pd.notna(row['volume']) else 0,
            daily_return=row.get('daily_return'),
            ma_7=row.get('ma_7'),
            ma_20=row.get('ma_20'),
            high_52w=row.get('high_52w'),
            low_52w=row.get('low_52w'),
            volatility_score=row.get('volatility_score'),
        )
        records.append(record)
    
    db.bulk_save_objects(records)
    db.commit()
    print(f"  💾 Stored {len(records)} records for {symbol}")


def collect_all_data():
    """
    Main data collection pipeline.
    Fetches, cleans, calculates metrics, and stores data for all configured stocks.
    
    First attempts yfinance; if that fails, uses synthetic data generation
    with Geometric Brownian Motion for realistic price simulation.
    """
    print("=" * 60)
    print("🚀 Stock Data Intelligence — Data Collection Pipeline")
    print("=" * 60)
    
    init_db()
    db = SessionLocal()
    
    success_count = 0
    fail_count = 0
    live_count = 0
    synthetic_count = 0
    
    for symbol, info in STOCK_SYMBOLS.items():
        print(f"\n📊 Processing {info['name']} ({symbol})...")
        
        # Step 1: Try to fetch live data
        df = fetch_stock_data(symbol)
        
        if df is None or (isinstance(df, pd.DataFrame) and df.empty):
            # Fallback: generate synthetic data
            print(f"  🔄 Generating synthetic data for {symbol}...")
            df = generate_synthetic_stock_data(symbol, info)
            synthetic_count += 1
        else:
            live_count += 1
        
        # Step 2: Clean data
        df = clean_data(df)
        if df.empty:
            fail_count += 1
            continue
        
        # Step 3: Calculate metrics
        df = calculate_metrics(df)
        
        # Step 4: Generate sentiment
        df = generate_sentiment_index(df)
        
        # Step 5: Store in database
        store_data(db, symbol, info, df)
        success_count += 1
        
        # Small delay to be respectful to Yahoo's API
        time.sleep(0.5)
    
    db.close()
    
    print("\n" + "=" * 60)
    print(f"✅ Pipeline Complete!")
    print(f"   📈 Live data: {live_count} stocks")
    print(f"   🔄 Synthetic data: {synthetic_count} stocks")
    print(f"   ❌ Failed: {fail_count} stocks")
    print(f"   📊 Total stored: {success_count} stocks")
    print("=" * 60)
    
    return success_count, fail_count


if __name__ == "__main__":
    collect_all_data()
