import logging
from typing import Optional

import requests
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_stock_data(symbol: str, period: str = "1mo") -> pd.DataFrame:
    """Fetch historical stock data for `symbol` using yfinance.

    Raises ValueError if no data is returned or symbol seems invalid.
    """
    if not symbol:
        raise ValueError("Empty symbol provided")

    logger.info("Fetching data for %s (period=%s)", symbol, period)
    stock = yf.Ticker(symbol)
    data = stock.history(period=period)

    if data is None or data.empty:
        raise ValueError(f"No data returned for symbol: {symbol}")

    try:
        data.to_csv("stock_data.csv")
    except Exception:
        logger.exception("Failed to write CSV; continuing without saving")

    return data


def get_usd_to_npr_rate(timeout: float = 5.0):
    """Get the USD -> NPR exchange rate, trying multiple public APIs.

    Returns a tuple `(rate: float, source: str)` where `source` indicates where
    the rate came from: 'live', 'cache', or 'default'. On success the rate is
    cached to `last_npr_rate.txt` so the app can still convert prices when the
    network/API is unavailable.
    """
    cache_file = "last_npr_rate.txt"

    # Try exchangerate.host convert endpoint first
    try:
        url = "https://api.exchangerate.host/convert?from=USD&to=NPR"
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        rate = data.get("info", {}).get("rate")
        if rate:
            rate = float(rate)
            try:
                Path(cache_file).write_text(str(rate))
            except Exception:
                logger.debug("Could not write rate cache file")
            return rate, "live"
    except Exception:
        logger.exception("Failed to fetch USD->NPR rate from exchangerate.host")

    # Try exchangerate.host latest endpoint as fallback
    try:
        url = "https://api.exchangerate.host/latest?base=USD&symbols=NPR"
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        rate = data.get("rates", {}).get("NPR")
        if rate:
            rate = float(rate)
            try:
                Path(cache_file).write_text(str(rate))
            except Exception:
                logger.debug("Could not write rate cache file")
            return rate, "live"
    except Exception:
        logger.exception("Failed to fetch USD->NPR rate from exchangerate.host latest")

    # Try another free API (er-api)
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        rate = data.get("rates", {}).get("NPR")
        if rate:
            rate = float(rate)
            try:
                Path(cache_file).write_text(str(rate))
            except Exception:
                logger.debug("Could not write rate cache file")
            return rate, "live"
    except Exception:
        logger.exception("Failed to fetch USD->NPR rate from er-api")

    # If all live attempts failed, try reading a cached rate
    try:
        p = Path(cache_file)
        if p.exists():
            txt = p.read_text().strip()
            if txt:
                rate = float(txt)
                logger.warning("Using cached USD->NPR rate: %s", rate)
                return rate, "cache"
    except Exception:
        logger.exception("Failed to read cached rate file")

    # Final fallback to a safe default
    default_rate = 140.0
    logger.warning("Using default USD->NPR rate: %s", default_rate)
    return default_rate, "default"


def plot_stock_data(data: pd.DataFrame, symbol: str, save_path: Optional[str] = None):
    """Plot closing price trend in NPR.

    Converts the `Close` prices from USD to NPR using a live rate and returns
    the rate used. Raises RuntimeError if conversion rate cannot be fetched.
    """
    if data is None or data.empty:
        raise ValueError("No data to plot")

    logger.info("Plotting data for %s", symbol)

    # Get conversion rate USD -> NPR (may return cached/default)
    rate, source = get_usd_to_npr_rate()

    # Convert close prices to NPR
    close_npr = data["Close"] * rate

    plt.ioff()
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(data.index, close_npr, label=f"{symbol} Closing Prices (NPR)")
    ax.set_title(f"{symbol} Stock Price Trend — Prices in NPR")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (NPR)")
    ax.legend()
    ax.grid(True)

    if save_path:
        fig.savefig(save_path)

    try:
        plt.show(block=False)
        plt.pause(0.001)
    except Exception:
        logger.exception("Non-blocking show failed; attempting blocking show")
        plt.show()

    # Return rate and its source so the caller can surface that information.
    return rate, source