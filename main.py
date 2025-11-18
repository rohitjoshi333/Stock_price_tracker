import tkinter as tk
from tkinter import messagebox
import tracker

root = tk.Tk()
root.title("📈 Stock Price Tracker")
root.geometry("420x150")
root.resizable(False, False)

# Create a container frame with padding so widgets are spaced from the window edges.
container = tk.Frame(root, padx=20, pady=10)
container.pack(expand=True, fill="both")

tk.Label(container, text="Stock Symbol (e.g., AAPL, TSLA, MSFT):").pack(pady=5)
symbol_entry = tk.Entry(container, width=40)
symbol_entry.pack()

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

tk.Button(container, text="Fetch & Plot Data", command=fetch_and_plot).pack(pady=10)

root.mainloop()
