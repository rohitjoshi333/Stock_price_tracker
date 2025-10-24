import tkinter as tk
from tkinter import messagebox
import tracker
import pandas as pd

root = tk.Tk()
root.title("📈 Stock Price Tracker")
root.geometry("420x400")
root.resizable(False, False)

tk.Label(root, text="Stock Symbol (e.g., AAPL, TSLA):").pack(pady=5)
symbol_entry = tk.Entry(root, width=40)
symbol_entry.pack()

tk.Label(root, text="Target Price (for Alert):").pack(pady=5)
target_entry = tk.Entry(root, width=40)
target_entry.pack()

tk.Label(root, text="Email (optional for alerts):").pack(pady=5)
email_entry = tk.Entry(root, width=40)
email_entry.pack()

def fetch_and_plot():
    symbol = symbol_entry.get().upper()
    if not symbol:
        messagebox.showerror("Error", "Please enter a stock symbol.")
        return

    try:
        data = tracker.fetch_stock_data(symbol)
        messagebox.showinfo("Success", f"Fetched {len(data)} records for {symbol}.")
        tracker.plot_stock_data(data, symbol)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch data: {e}")

def check_alert():
    symbol = symbol_entry.get().upper()
    target = target_entry.get()
    email = email_entry.get()

    if not symbol or not target:
        messagebox.showerror("Error", "Enter stock symbol and target price.")
        return

    try:
        target_price = float(target)
        message = tracker.check_price_and_alert(symbol, target_price, email)
        messagebox.showinfo("Alert", message)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to check alert: {e}")

tk.Button(root, text="Fetch & Plot Data", command=fetch_and_plot).pack(pady=10)
tk.Button(root, text="Check Price Alert", command=check_alert).pack(pady=10)

root.mainloop()
