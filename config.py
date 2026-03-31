"""
Configuration settings for the Stock Data Intelligence Dashboard.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Database
DATABASE_URL = f"sqlite:///{BASE_DIR / 'stock_data.db'}"

# Stock symbols - Major Indian companies on NSE
STOCK_SYMBOLS = {
    "RELIANCE.NS": {"name": "Reliance Industries", "sector": "Energy"},
    "TCS.NS": {"name": "Tata Consultancy Services", "sector": "IT"},
    "INFY.NS": {"name": "Infosys", "sector": "IT"},
    "HDFCBANK.NS": {"name": "HDFC Bank", "sector": "Banking"},
    "ICICIBANK.NS": {"name": "ICICI Bank", "sector": "Banking"},
    "HINDUNILVR.NS": {"name": "Hindustan Unilever", "sector": "FMCG"},
    "ITC.NS": {"name": "ITC Limited", "sector": "FMCG"},
    "SBIN.NS": {"name": "State Bank of India", "sector": "Banking"},
    "BHARTIARTL.NS": {"name": "Bharti Airtel", "sector": "Telecom"},
    "KOTAKBANK.NS": {"name": "Kotak Mahindra Bank", "sector": "Banking"},
    "LT.NS": {"name": "Larsen & Toubro", "sector": "Infrastructure"},
    "WIPRO.NS": {"name": "Wipro", "sector": "IT"},
    "HCLTECH.NS": {"name": "HCL Technologies", "sector": "IT"},
    "TATAMOTORS.NS": {"name": "Tata Motors", "sector": "Automobile"},
    "MARUTI.NS": {"name": "Maruti Suzuki", "sector": "Automobile"},
    "SUNPHARMA.NS": {"name": "Sun Pharmaceutical", "sector": "Pharma"},
    "TITAN.NS": {"name": "Titan Company", "sector": "Consumer"},
    "ADANIENT.NS": {"name": "Adani Enterprises", "sector": "Conglomerate"},
    "POWERGRID.NS": {"name": "Power Grid Corporation", "sector": "Utilities"},
    "NTPC.NS": {"name": "NTPC Limited", "sector": "Utilities"},
}

# Data collection settings
DATA_PERIOD = "1y"  # Fetch 1 year of data
DATA_INTERVAL = "1d"  # Daily data

# API settings
API_HOST = "0.0.0.0"
API_PORT = 8000

# Cache TTL (seconds)
CACHE_TTL = 3600  # 1 hour
