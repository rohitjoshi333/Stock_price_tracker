import logging
from typing import Optional

import requests
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

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


def get_usd_to_npr_rate(timeout: float = 5.0) -> float:
    """Get the USD -> NPR exchange rate from a free public API.

    Uses exchangerate.host which requires no API key. If the request fails,
    raises RuntimeError.
    """
    url = "https://api.exchangerate.host/convert?from=USD&to=NPR"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        rate = data.get("info", {}).get("rate")
        if not rate:
            raise RuntimeError("No rate returned from exchange API")
        return float(rate)
    except Exception as e:
        logger.exception("Failed to fetch USD->NPR rate: %s", e)
        raise RuntimeError("Failed to fetch exchange rate") from e


def plot_stock_data(data: pd.DataFrame, symbol: str, save_path: Optional[str] = None) -> float:
    """Plot closing price trend in NPR.

    Converts the `Close` prices from USD to NPR using a live rate and returns
    the rate used. Raises RuntimeError if conversion rate cannot be fetched.
    """
    if data is None or data.empty:
        raise ValueError("No data to plot")

    logger.info("Plotting data for %s", symbol)

    # Get conversion rate USD -> NPR
    rate = get_usd_to_npr_rate()

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

    return rate