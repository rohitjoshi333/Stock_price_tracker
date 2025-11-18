import logging
from typing import Optional

import requests
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib import dates as mdates
from matplotlib import ticker as mticker

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


def plot_stock_data(data: pd.DataFrame, symbol: str, ax=None, save_path: Optional[str] = None):
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

    # Improve styling for readability
    try:
        plt.style.use("seaborn-darkgrid")
    except Exception:
        pass

    # If no axes provided, create a new figure/axes and we will show it.
    created_fig = False
    if ax is None:
        plt.ioff()
        fig, ax = plt.subplots(figsize=(11, 5), dpi=100)
        created_fig = True
    else:
        fig = ax.figure

    # plot main line
    line = ax.plot(data.index, close_npr, label=f"{symbol} Closing Prices (NPR)", linewidth=2.5, color="#1f77b4")[0]
    # plot a short moving average to show trend
    try:
        ma = close_npr.rolling(window=7, min_periods=1).mean()
        ax.plot(data.index, ma, label="7-day MA", linewidth=1.6, color="#ff7f0e", alpha=0.9)
    except Exception:
        ma = None

    # gentle area fill under the curve for emphasis
    ax.fill_between(data.index, close_npr, alpha=0.08, color="#1f77b4")

    # Highlight latest value
    last_date = data.index[-1]
    last_val = float(close_npr.iloc[-1])
    ax.scatter([last_date], [last_val], color="#d62728", zorder=6)
    ax.annotate(f"Rs {last_val:,.2f}", xy=(last_date, last_val), xytext=(-80, 12), textcoords="offset points",
                arrowprops=dict(arrowstyle="->", color="#555555"), bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.9), fontsize=10)

    # Titles and labels
    ax.set_title(f"{symbol} Stock Price Trend — Prices in NPR", fontsize=14, weight="bold")
    ax.set_xlabel("Date", fontsize=11)
    ax.set_ylabel("Price (NPR)", fontsize=11)

    # Format x-axis dates and rotate for readability
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    for label in ax.get_xticklabels():
        label.set_rotation(30)
        label.set_horizontalalignment('right')

    # Format y-axis with thousand separators and INR symbol
    def yfmt(x, pos):
        if abs(x) >= 1000:
            return f"Rs {x:,.0f}"
        return f"Rs {x:,.2f}"

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(yfmt))

    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.6)

    # Try to enable hover tooltips with mplcursors if available
    try:
        import mplcursors

        cursor = mplcursors.cursor(line, hover=True)

        @cursor.connect("add")
        def _(sel):
            y = sel.target[1]
            sel.annotation.set_text(f"Rs {y:,.2f}")
            sel.annotation.get_bbox_patch().set_alpha(0.9)
    except Exception:
        logger.debug("mplcursors not available or failed to attach; skipping hover tooltips")

    if save_path:
        fig.savefig(save_path)

    # If we created the figure locally, show it non-blocking as before. If
    # the caller provided axes (embedding in a GUI), we won't call show here.
    if created_fig:
        try:
            plt.show(block=False)
            plt.pause(0.001)
        except Exception:
            logger.exception("Non-blocking show failed; attempting blocking show")
            plt.show()

    # Return rate, source and the used figure/axes so the caller can embed them.
    return rate, source, fig, ax