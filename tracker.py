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

# Send email alert (optional)
def send_email_alert(stock_name, current_price, target_price, receiver_email):
    sender_email = "your_email@gmail.com"
    sender_password = "your_app_password"  # Use Gmail app password

    subject = f"Stock Alert: {stock_name} Price Update"
    body = f"{stock_name} current price is ${current_price:.2f}, which crossed your target ${target_price:.2f}."

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print("✅ Email alert sent!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# Check price and alert
def check_price_and_alert(symbol, target_price, receiver_email):
    stock = yf.Ticker(symbol)
    current_price = stock.history(period="1d")["Close"].iloc[-1]

    if current_price >= target_price:
        send_email_alert(symbol, current_price, target_price, receiver_email)
        return f"Alert sent! {symbol} reached ${current_price:.2f}"
    else:
        return f"{symbol} current price ${current_price:.2f} is below target ${target_price:.2f}"
