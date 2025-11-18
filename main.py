import re
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import tracker
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)


def load_symbols(file_path="Stock_Symbols.txt"):
    path = Path(file_path)
    symbols = []
    if path.exists():
        txt = path.read_text()
        # Extract symbols wrapped in **SYMBOL** in the markdown-style file
        symbols = re.findall(r"\*\*([A-Z0-9\-\^]+)\*\*", txt)
    if not symbols:
        # fallback commonly used symbols
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    return sorted(set(symbols))


class StockTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("📈 Stock Price Tracker")
        self.geometry("480x180")
        self.resizable(False, False)

        container = tk.Frame(self, padx=16, pady=12)
        container.pack(expand=True, fill="both")

        tk.Label(container, text="Stock Symbol:").grid(row=0, column=0, sticky="w")

        self.symbol_var = tk.StringVar()
        symbols = load_symbols()
        self.symbol_combobox = ttk.Combobox(container, textvariable=self.symbol_var, values=symbols)
        self.symbol_combobox.set(symbols[0])
        self.symbol_combobox.grid(row=0, column=1, padx=8, pady=6, sticky="ew")

        self.fetch_btn = ttk.Button(container, text="Fetch & Plot", command=self.on_fetch_clicked)
        self.fetch_btn.grid(row=1, column=0, columnspan=2, pady=8)

        # status bar
        self.status_var = tk.StringVar(value="Idle")
        status_label = ttk.Label(container, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        status_label.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        container.columnconfigure(1, weight=1)

    def set_status(self, text):
        self.status_var.set(text)

    def on_fetch_clicked(self):
        symbol = self.symbol_var.get().strip().upper()
        if not symbol:
            messagebox.showerror("Error", "Please select or enter a stock symbol.")
            return

        # disable UI while fetching
        self.fetch_btn.config(state="disabled")
        self.set_status(f"Fetching {symbol}...")

        thread = threading.Thread(target=self._fetch_thread, args=(symbol,), daemon=True)
        thread.start()

    def _fetch_thread(self, symbol):
        try:
            data = tracker.fetch_stock_data(symbol)
            # schedule UI updates on main thread
            self.after(0, self._on_fetch_success, symbol, data)
        except Exception as exc:
            logging.exception("Error fetching data")
            self.after(0, self._on_fetch_error, exc)

    def _on_fetch_success(self, symbol, data):
        self.set_status(f"Fetched {len(data)} records for {symbol}.")
        # Re-enable button
        self.fetch_btn.config(state="normal")
        try:
            tracker.plot_stock_data(data, symbol)
            self.set_status(f"Plot displayed for {symbol}.")
        except Exception as e:
            logging.exception("Plotting failed")
            messagebox.showerror("Error", f"Plotting failed: {e}")

    def _on_fetch_error(self, exc):
        self.fetch_btn.config(state="normal")
        self.set_status("Error")
        messagebox.showerror("Error", f"Failed to fetch data: {exc}")


if __name__ == "__main__":
    app = StockTrackerApp()
    app.mainloop()
