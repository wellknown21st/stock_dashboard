# 📊 Stock Data Intelligence Dashboard

A comprehensive financial data intelligence platform that collects, analyzes, and visualizes Indian stock market data (NSE) with AI-powered price predictions.

![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=flat-square&logo=fastapi&logoColor=white)
![Chart.js](https://img.shields.io/badge/Chart.js-4.4-ff6384?style=flat-square&logo=chart.js&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003b57?style=flat-square&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ed?style=flat-square&logo=docker&logoColor=white)

---

## 🚀 Features

### 📈 Data Collection & Analysis
- **Real-time data** from Yahoo Finance (yfinance) for **20+ NSE-listed companies**
- **Automated data cleaning** — handles missing values, duplicates, formatting issues
- **Calculated metrics**: Daily Return, 7-day & 20-day Moving Averages, 52-week High/Low
- **Custom analytics**: Volatility Score, Sentiment Index, Correlation Matrix

### 🔌 REST API (FastAPI)
| Endpoint | Method | Description |
|---|---|---|
| `/api/companies` | GET | List all available companies |
| `/api/data/{symbol}` | GET | Historical stock data (configurable days) |
| `/api/summary/{symbol}` | GET | 52-week high/low, average close, trend analysis |
| `/api/compare` | GET | Compare two stocks' performance |
| `/api/gainers` | GET | Top gaining stocks |
| `/api/losers` | GET | Top losing stocks |
| `/api/volatility` | GET | Most volatile stocks |
| `/api/sectors` | GET | Sector-wise performance |
| `/api/predict/{symbol}` | GET | AI price prediction (Linear Regression) |
| `/api/correlation` | GET | Cross-stock correlation matrix |

📖 **Interactive API docs** available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

### 🎨 Visualization Dashboard
- **Premium dark theme** with glassmorphism and smooth animations
- **Interactive charts** (Chart.js) — closing prices, volume, moving averages
- **Company sidebar** with search and live price indicators
- **Time filters**: 1W, 1M, 3M, 6M, 1Y
- **Stock comparison** with normalized performance overlay
- **Sector performance** overview
- **Top Gainers/Losers** widget
- **Correlation heatmap** — visualize how stocks move together

### 🧠 AI/ML Features
- **Linear Regression** price prediction for next 7 days
- Model performance metrics (R² scores)
- Visual chart combining historical data with prediction line
- ⚠️ Educational purposes only — not financial advice

### ⚡ Extra Features
- 🐳 **Docker support** for easy deployment
- 📊 **Swagger docs** auto-generated
- 🔄 **Data refresh** capability
- 📱 **Responsive design** — works on mobile
- 🔎 **Search & filter** companies

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.11+ |
| **Backend** | FastAPI + Uvicorn |
| **Database** | SQLite (via SQLAlchemy) |
| **Data Processing** | Pandas, NumPy |
| **Data Source** | yfinance (Yahoo Finance) |
| **ML/AI** | scikit-learn (Linear Regression) |
| **Frontend** | HTML5 + Vanilla JS + CSS3 |
| **Charts** | Chart.js 4.4 |
| **Font** | Inter (Google Fonts) |
| **Containerization** | Docker + Docker Compose |

---

## 📋 Setup & Installation

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- Internet connection (to fetch stock data)

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/stock-data-intelligence-dashboard.git
cd stock-data-intelligence-dashboard
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Collect Stock Data
```bash
python data_collector.py
```
This fetches 1 year of historical data for 20 NSE-listed companies and stores it in `stock_data.db`.

### Step 5: Start the Server
```bash
python main.py
```
or
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 6: Open the Dashboard
Navigate to: **http://localhost:8000**

API Docs: **http://localhost:8000/docs**

---

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)
```bash
docker-compose up --build
```

### Using Docker directly
```bash
docker build -t stock-intel-dashboard .
docker run -p 8000:8000 stock-intel-dashboard
```

---

## 📂 Project Structure

```
stock-data-intelligence-dashboard/
├── main.py                  # FastAPI application (all endpoints)
├── data_collector.py        # Data fetching, cleaning, metrics pipeline
├── predictor.py             # ML prediction module (Linear Regression)
├── database.py              # SQLAlchemy models and DB setup
├── config.py                # Configuration (symbols, settings)
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose setup
├── .gitignore
├── README.md
└── static/
    ├── index.html           # Dashboard UI
    ├── styles.css           # Premium dark theme styles
    └── app.js               # Frontend logic & chart rendering
```

---

## 🧪 How It Works

### Data Pipeline
```
Yahoo Finance API → yfinance → Raw DataFrame
      ↓
Clean Data (handle NaN, fix dates, remove invalid rows)
      ↓
Calculate Metrics (Daily Return, MAs, 52W High/Low, Volatility)
      ↓
Generate Sentiment Index (momentum + volume-based)
      ↓
Store in SQLite (stock_data.db)
```

### Custom Metrics

1. **Daily Return** = `(Close - Open) / Open` — measures intraday price change
2. **7-Day Moving Average** — smooths short-term price fluctuations
3. **20-Day Moving Average** — captures medium-term trend
4. **52-Week High/Low** — rolling max/min over 252 trading days
5. **Volatility Score** — rolling standard deviation of daily returns (20-day window)
6. **Sentiment Index** (Custom) — combines price momentum, volume trends, and MA crossovers to produce a -1.0 to +1.0 sentiment score

### ML Prediction Model
- **Algorithm**: Linear Regression (scikit-learn)
- **Features**: Lagged prices (5-day), moving averages, volume, price range, daily return
- **Target**: Next-day closing price
- **Evaluation**: R² score on train/test split (80/20)
- **Output**: 7-day forward predictions with confidence metrics

---

## 📊 Companies Covered (20 NSE Stocks)

| Symbol | Company | Sector |
|---|---|---|
| RELIANCE | Reliance Industries | Energy |
| TCS | Tata Consultancy Services | IT |
| INFY | Infosys | IT |
| HDFCBANK | HDFC Bank | Banking |
| ICICIBANK | ICICI Bank | Banking |
| HINDUNILVR | Hindustan Unilever | FMCG |
| ITC | ITC Limited | FMCG |
| SBIN | State Bank of India | Banking |
| BHARTIARTL | Bharti Airtel | Telecom |
| KOTAKBANK | Kotak Mahindra Bank | Banking |
| LT | Larsen & Toubro | Infrastructure |
| WIPRO | Wipro | IT |
| HCLTECH | HCL Technologies | IT |
| TATAMOTORS | Tata Motors | Automobile |
| MARUTI | Maruti Suzuki | Automobile |
| SUNPHARMA | Sun Pharmaceutical | Pharma |
| TITAN | Titan Company | Consumer |
| ADANIENT | Adani Enterprises | Conglomerate |
| POWERGRID | Power Grid Corporation | Utilities |
| NTPC | NTPC Limited | Utilities |

---

## 🧠 Design Decisions & Insights

### Why SQLite?
- Zero setup, portable, suitable for this project scale
- Entire database in a single file (`stock_data.db`)
- Perfect for local development and demo purposes

### Why yfinance?
- Free, no API key required
- Reliable data for Indian NSE stocks
- Easy to use with Pandas integration

### Why Chart.js?
- Lightweight, performant, and highly customizable
- Beautiful default animations
- Good interactivity (hover, tooltips, responsiveness)

### Why Linear Regression for Prediction?
- Interpretable, fast, educational
- Demonstrates the concept of feature engineering
- Model metrics (R²) provide transparency about accuracy
- Clear disclaimer that it's not financial advice

---

## ⚠️ Disclaimer

This project is built for **educational and demonstrative purposes only**. The AI predictions are generated by a simplified Linear Regression model and should **NOT** be used for actual financial decisions. Always consult a certified financial advisor before making investment decisions.

---

## 👤 Author

**Mayank Mishra**

---

## 📜 License

This project is open-source and available under the [MIT License](LICENSE).
