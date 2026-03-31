"""
Database models and connection setup using SQLAlchemy.
"""

from sqlalchemy import create_engine, Column, String, Float, Date, Integer, BigInteger, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class StockData(Base):
    """Model representing daily stock data for a company."""
    __tablename__ = "stock_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    company_name = Column(String(100), nullable=False)
    sector = Column(String(50), nullable=False)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(BigInteger)

    # Calculated metrics
    daily_return = Column(Float)        # (Close - Open) / Open
    ma_7 = Column(Float)               # 7-day Moving Average
    ma_20 = Column(Float)              # 20-day Moving Average
    high_52w = Column(Float)           # 52-week High
    low_52w = Column(Float)            # 52-week Low
    volatility_score = Column(Float)   # Custom: Rolling std of daily returns

    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='uix_symbol_date'),
    )


def init_db():
    """Initialize the database and create tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
