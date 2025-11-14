import yfinance as yf
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import matplotlib.pyplot as plt

# Fetch stock data
def fetch_stock_data(symbol, period="1mo"):
    stock = yf.Ticker(symbol)
    data = stock.history(period=period)
    data.to_csv("stock_data.csv")
    return data

# Plot price trend
def plot_stock_data(data, symbol):
    plt.figure(figsize=(8, 4))
    plt.plot(data["Close"], label=f"{symbol} Closing Prices")
    plt.title(f"{symbol} Stock Price Trend")
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    plt.legend()
    plt.grid(True)
    plt.show()