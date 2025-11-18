import logging
from typing import Optional

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


def plot_stock_data(data: pd.DataFrame, symbol: str, save_path: Optional[str] = None):
    """Plot closing price trend for a fetched dataset.

    Uses non-blocking show where possible (`block=False`). If `save_path` is given,
    the plot will also be saved to that file.
    """
    if data is None or data.empty:
        raise ValueError("No data to plot")

    logger.info("Plotting data for %s", symbol)
    plt.ioff()
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(data.index, data["Close"], label=f"{symbol} Closing Prices")
    ax.set_title(f"{symbol} Stock Price Trend")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")
    ax.legend()
    ax.grid(True)

    if save_path:
        fig.savefig(save_path)

    try:
        # Try to show non-blocking; some backends may still block.
        plt.show(block=False)
        # brief pause to allow the window to render in some environments
        plt.pause(0.001)
    except Exception:
        logger.exception("Non-blocking show failed; attempting blocking show")
        plt.show()