import yfinance as yf
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import requests
import logging
from models import StockPrice, AssetData, setup_database
from flask import Flask, Response

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

def create_engine_from_env():
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_name = os.getenv("DB_NAME")
    
    required_vars = {"DB_USER": db_user, "DB_PASSWORD": db_password, "DB_NAME": db_name}
    missing_vars = [key for key, value in required_vars.items() if not value]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return None
    
    db_url = f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}"
    try:
        engine = create_engine(db_url, echo=False)
        logger.info("Database engine created successfully")
        return engine
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

def get_yahoo_price(yahoo_code):
    try:
        stock = yf.Ticker(yahoo_code)
        price = stock.history(period="1d")['Close'].iloc[-1]
        return price
    except Exception as e:
        logger.error(f"Error fetching Yahoo price for {yahoo_code}: {e}")
        return None

def get_dexscreener_price(chain, pair_address):
    url = f'https://api.dexscreener.com/latest/dex/pairs/{chain}/{pair_address}'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if 'pairs' in data and data['pairs']:
            pair = data['pairs'][0]
            return float(pair['priceUsd'])
        else:
            logger.warning("No pair data found in Dexscreener response")
            return None
    except Exception as e:
        logger.error(f"Error fetching Dexscreener price for {chain}/{pair_address}: {e}")
        return None

def save_price_to_db(session, symbol, price):
    if price is not None:
        try:
            existing_price = session.query(StockPrice).filter_by(symbol=symbol).first()
            if existing_price:
                existing_price.price = price
                existing_price.timestamp = datetime.utcnow()
            else:
                new_price = StockPrice(symbol=symbol, price=price)
                session.add(new_price)
            session.commit()
            logger.info(f"Updated {symbol}: {price} at {datetime.utcnow()}")
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            session.rollback()
    else:
        logger.warning(f"Skipping save for {symbol} due to invalid price")

@app.route('/', methods=['GET'])
def update_prices():
    logger.info("Received request to update prices")
    engine = create_engine_from_env()
    if engine is None:
        return Response("Database connection failed", status=500)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        setup_database(engine)
        
        assets = session.query(AssetData).all()
        if not assets:
            logger.warning("No assets found in AssetData table")
        else:
            for asset in assets:
                price = get_yahoo_price(asset.yahooCode)
                save_price_to_db(session, asset.symbol, price)
        
        bera_chain = 'berachain'
        bera_pair_address = '0x90f79fdec42351e514c35cd93cb5f1b965585132'
        bera_price = get_dexscreener_price(bera_chain, bera_pair_address)
        save_price_to_db(session, 'BERA', bera_price)
        
        logger.info("Price update completed")
        return Response("Prices updated successfully", status=200)
    except Exception as e:
        logger.error(f"Error in update_prices: {e}")
        return Response(f"Error: {str(e)}", status=500)
    finally:
        session.close()
        engine.dispose()

if __name__ == "__main__":
    try:
        port = int(os.getenv("PORT", 8080))
        logger.info(f"Starting Flask on port {port}")
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        logger.error(f"Failed to start Flask: {e}")
        raise