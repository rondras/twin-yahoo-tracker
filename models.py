from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

# Define the SQLAlchemy Base
Base = declarative_base()

class StockPrice(Base):
    __tablename__ = 'stock_prices'
    
    symbol = Column(String(10), primary_key=True)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class AssetData(Base):
    __tablename__ = 'assetData'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    yahooCode = Column(String(50), nullable=False)
    
    def __repr__(self):
        return f"<AssetData(symbol={self.symbol}, name={self.name}, yahooCode={self.yahooCode})>"

def setup_database(engine):
    """Create all tables defined in models if they don't exist"""
    try:
        Base.metadata.create_all(engine)
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise