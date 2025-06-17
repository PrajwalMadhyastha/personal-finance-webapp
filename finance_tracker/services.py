# finance_tracker/services.py
import os
import requests
import logging
import time
from flask import current_app

# Set up a logger for this module
logger = logging.getLogger(__name__)

# Alpha Vantage API base URL
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# A small cache to avoid re-fetching the same ticker in a single request
# For a production app, a more robust solution like Redis or Flask-Caching would be ideal.
price_cache = {}


def get_stock_price(ticker_symbol):
    """
    Fetches the latest stock price for a given ticker symbol from Alpha Vantage.
    Includes basic caching and rate-limit handling.
    """
    if ticker_symbol in price_cache:
        return price_cache[ticker_symbol]

    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        logger.error("ALPHA_VANTAGE_API_KEY not set in environment.")
        return None

    params = {"function": "GLOBAL_QUOTE", "symbol": ticker_symbol, "apikey": api_key}

    try:
        # Introduce a small delay to be considerate to the API's free tier limits
        time.sleep(1)  # A 1-second delay between requests

        response = requests.get(
            ALPHA_VANTAGE_BASE_URL, params=params, timeout=10
        )  # 10-second timeout
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        data = response.json()

        # Check for API-specific error messages or rate limit notifications
        if "Note" in data:
            logger.warning(
                f"Alpha Vantage API note for {ticker_symbol}: {data['Note']}"
            )
            # This indicates we might be hitting the rate limit, so we stop trying for now.
            return None

        # Check if the required data is in the response
        if "Global Quote" not in data or "05. price" not in data["Global Quote"]:
            logger.warning(f"Unexpected API response for {ticker_symbol}: {data}")
            price_cache[ticker_symbol] = None  # Cache the failure to avoid retries
            return None

        price_str = data["Global Quote"]["05. price"]
        price = float(price_str)

        price_cache[ticker_symbol] = price  # Cache the successful result
        return price

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching stock price for {ticker_symbol}: {e}")
        return None
    except (ValueError, KeyError) as e:
        logger.error(f"Error parsing stock price data for {ticker_symbol}: {e}")
        return None
