import yfinance as yf
import requests
import pandas as pd
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class Asset:
    def __init__(self, name, amount, value, currency, pp_unit):
        self.name = name
        self.amount = amount
        self.value = value
        self.currency = currency
        self.pp_unit = pp_unit
    
    def get_type(self):
        raise NotImplementedError
    
    def to_dictionary(self):
        return {
            "type": self.get_type(),
            "amount": self.amount,
            "value": self.value,
            "currency": self.currency,
            "pp_unit": self.pp_unit
        }
    

class Crypto(Asset):
    coin_aliases = {
        "btc": "bitcoin",
        "bitcoin": "bitcoin",
        "eth": "ethereum",
        "ethereum": "ethereum",
        "cro": "crypto-com-chain",
        "crypto.com": "crypto-com-chain",
        "sol": "solana",
        "solana": "solana"
    }

    def get_type(self):
        return "crypto"
    
    @staticmethod
    def crypto_price(coin_id, currency):
        try:
            url_coingecko = "https://api.coingecko.com/api/v3/simple/price"
            params = {'ids': coin_id, 'vs_currencies': currency}
            response = requests.get(url_coingecko, params=params)

            if response.status_code == 200:
                data = response.json()
                return data[coin_id][currency]
            else:
                return None
        except Exception as e:
            print(f"Error fetching crypto price: {e}")
            return None
    
    @staticmethod
    def crypto_historical_price(coin_id, currency, date):
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            date_format = date_obj.strftime("%d-%m-%Y")

            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/history"
            params = {'date': date_format}
            response = requests.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                return data['market_data']['current_price'].get(currency)
            else:
                return None
        except Exception as e:
            print(f"Error fetching historical price: {e}")
            return None
        

class Stock(Asset):

    def get_type(self):
        return "stock"

    @staticmethod
    def stock_price(stock_name, currency):
        try:
            stock = yf.Ticker(stock_name)
            stock_price_usd = stock.fast_info['last_price']

            if stock_price_usd is None:
                return None
            
            if currency.upper() == "USD":
                return stock_price_usd
            
            forex_pair = f"{currency.upper()}USD=X"
            forex = yf.Ticker(forex_pair)
            exchange_rate = forex.fast_info['last_price'] 

            if exchange_rate:
                return stock_price_usd / exchange_rate
            else:
                return None
        except Exception as e:
            print(f"Error fetching stock price: {e}")
            return None
        
    @staticmethod
    def stock_historical_price(stock_name, currency, date):
        try:
            stock = yf.Ticker(stock_name)
            hist = stock.history(start=date, end=date)

            if hist.empty:
                return None
            
            stock_price_usd = hist['Close'].iloc[0]
            if currency.upper() == "USD":
                return stock_price_usd

            forex_pair = f"{currency.upper()}USD=X"
            forex = yf.Ticker(forex_pair)
            forex_hist = forex.history(start=date, end=date)

            if not forex_hist.empty:
                exchange_rate = forex_hist['Close'].iloc[0]
                return stock_price_usd / exchange_rate
            else:
                return None
        except Exception as e:
            print(f"Error fetching historical stock price: {e}")
            return None


#class Cash(Asset):
    #def get_type(self):
        #print("cash")




class Portfolio:
    def __init__(self):
        self.assets = {}
        self.currency = None

    def set_currency(self, currency):
        self.currency = currency.lower()
        print(f"Currency set to {self.currency.upper()}")

    def add_asset(self, name, asset):
        self.assets[name] = asset

    def update_existing_asset(self, name, amount_to_add, value_to_add):
        if name in self.assets:
            self.assets[name].amount += amount_to_add
            self.assets[name].value += value_to_add
            return True
        return False
    
    def remove_asset(self, name):
        if name in self.assets:
            del self.assets[name]
            return True
        return False

    def update_asset_amount(self, name, new_amount):
        if name in self.assets:
            asset = self.assets[name]
            old_amount = asset.amount
            old_value = asset.value

            asset.amount = new_amount
            asset.value = (old_value / old_amount) * new_amount
            return True
        else:
            return False
        
    def asset_exists(self, name):
        return name in self.assets

    def display(self):
        if not self.assets:
            print("Portfolio is empty")
            return
        
        total_current_value = 0
        total_purchase_value = 0
        print("\n-------PORTFOLIO TOTAL:------\n")

        for name, asset in self.assets.items():
            if asset.get_type() == "crypto":
                current_price = Crypto.crypto_price(name, self.currency)
            else:
                current_price = Stock.stock_price(asset.name, self.currency)
            
            if current_price:
                current_value = asset.amount * current_price
                purchase_value = asset.amount * asset.pp_unit
                profit_loss = current_value - purchase_value
                profit_loss_pct = (profit_loss / purchase_value * 100) if purchase_value > 0 else 0
                
                print(f"{name.capitalize()} ({asset.get_type()}):")
                print(f"  Amount: {asset.amount} units")
                print(f"  Purchase Price: {asset.currency} {asset.pp_unit:.2f} per unit")
                print(f"  Current Price: {asset.currency} {current_price:.2f} per unit")
                print(f"  Total Invested: {asset.currency} {purchase_value:.2f}")
                print(f"  Current Value: {asset.currency} {current_value:.2f}")
                print(f"  Profit/Loss: {asset.currency} {profit_loss:+.2f} ({profit_loss_pct:+.2f}%)\n")
                
                total_current_value += current_value
                total_purchase_value += purchase_value
            else:
                print(f"{name.capitalize()} ({asset.get_type()}): {asset.amount} units = {asset.currency} {asset.value:.2f} (Could not fetch current price)\n")
                total_current_value += asset.value
                total_purchase_value += asset.value

        total_profit_loss = total_current_value - total_purchase_value
        total_profit_loss_pct = (total_profit_loss / total_purchase_value * 100) if total_purchase_value > 0 else 0
        
        print("="*50)
        print(f"Total Invested: {self.currency.upper()} {total_purchase_value:.2f}")
        print(f"Total Current Value: {self.currency.upper()} {total_current_value:.2f}")
        print(f"Total Profit/Loss: {self.currency.upper()} {total_profit_loss:+.2f} ({total_profit_loss_pct:+.2f}%)")
        print("="*50 + "\n")

    def export_to_csv(self, filename="portfolio.csv"):
        if not self.assets:
            print("Portfolio is empty, please add some assets")
            return
        else:
            data_rows = []
            for name, asset in self.assets.items():
                if asset.get_type() == "crypto":
                    current_price = Crypto.crypto_price(name, self.currency)
                else:
                    current_price = Stock.stock_price(asset.name, self.currency)
                
                if current_price:
                    current_value = asset.amount * current_price
                    purchase_value = asset.amount * asset.pp_unit
                    profit_loss = current_value - purchase_value
                else:
                    current_value = asset.value
                    purchase_value = asset.value
                    profit_loss = 0
                
                data_rows.append({
                    "Asset Name": name,
                    "Type of Asset": asset.get_type(),
                    "Amount": asset.amount,
                    "Purchase Price Per Unit": asset.pp_unit,
                    "Current Price Per Unit": current_price if current_price else "N/A",
                    "Total Invested": purchase_value,
                    "Current Value": current_value,
                    "Profit/Loss": profit_loss,
                    "Currency": asset.currency
                })
            
            df = pd.DataFrame(data_rows)
            df.to_csv(filename, index=False)
            print(f"✅ {filename} created successfully!")

    def is_empty(self):
        return len(self.assets) == 0
    

class PortfolioApp:

    def __init__(self):
        self.portfolio = Portfolio()

    def add_crypto(self):
        print("You selected crypto.")
        crypto_input = input("Type the crypto name: \n").strip().lower()
        crypto_amount = float(input(f"How much {crypto_input.upper()} do you own? \n"))

        if crypto_input in Crypto.coin_aliases:
            coin_id = Crypto.coin_aliases[crypto_input]
            
            choice = input("Do you want to:\n1. Enter purchase date (e.g., 2024-07-04)\n2. Enter purchase price manually\nChoice: ").strip()
            
            if choice == "1":
                purchase_date = input("Enter purchase date (YYYY-MM-DD): ").strip()
                purchase_price = Crypto.crypto_historical_price(coin_id, self.portfolio.currency, purchase_date)
                
                if purchase_price:
                    print(f"Historical price on {purchase_date}: {self.portfolio.currency.upper()} {purchase_price:.2f}")
                else:
                    print("Could not fetch historical price. Please enter manually.")
                    purchase_price = float(input(f"Enter purchase price per {crypto_input.upper()}: "))
            else:
                purchase_price = float(input(f"Enter purchase price per {crypto_input.upper()}: "))
            
            current_price = Crypto.crypto_price(coin_id, self.portfolio.currency)

            if current_price:
                current_total_value = crypto_amount * current_price
                purchase_total_value = crypto_amount * purchase_price
                profit_loss = current_total_value - purchase_total_value
                
                print(f"\nAdded {crypto_amount} {coin_id.capitalize()}")
                print(f"Purchase price: {self.portfolio.currency.upper()} {purchase_price:.2f} per unit")
                print(f"Current price: {self.portfolio.currency.upper()} {current_price:.2f} per unit")
                print(f"Total invested: {self.portfolio.currency.upper()} {purchase_total_value:.2f}")
                print(f"Current value: {self.portfolio.currency.upper()} {current_total_value:.2f}")
                print(f"Profit/Loss: {self.portfolio.currency.upper()} {profit_loss:+.2f}\n")

                crypto_asset = Crypto(coin_id, crypto_amount, current_total_value, self.portfolio.currency.upper(), purchase_price)
                self.portfolio.add_asset(coin_id, crypto_asset)
            else:
                print("Failed to get current price")
        else:
            print("Unknown crypto, check the name or type another one")

    def add_stock(self):
        print("You selected stock:")
        stock_name = input("Type the stock ticker: ").upper()
        stock_amount = float(input(f"How much of {stock_name} do you own? "))

        choice = input("Do you want to:\n1. Enter purchase date (e.g., 2024-07-04)\n2. Enter purchase price manually\nChoice: ").strip()
        
        if choice == "1":
            purchase_date = input("Enter purchase date (YYYY-MM-DD): ").strip()
            purchase_price = Stock.stock_historical_price(stock_name, self.portfolio.currency, purchase_date)
            
            if purchase_price:
                print(f"Historical price on {purchase_date}: {self.portfolio.currency.upper()} {purchase_price:.2f}")
            else:
                print("Could not fetch historical price. Please enter manually.")
                purchase_price = float(input(f"Enter purchase price per share of {stock_name}: "))
        else:
            purchase_price = float(input(f"Enter purchase price per share of {stock_name}: "))

        current_price = Stock.stock_price(stock_name, self.portfolio.currency)

        if current_price:
            current_total_value = stock_amount * current_price
            purchase_total_value = stock_amount * purchase_price
            profit_loss = current_total_value - purchase_total_value
            
            print(f"\n{stock_amount} shares of {stock_name}")
            print(f"Purchase price: {self.portfolio.currency.upper()} {purchase_price:.2f} per share")
            print(f"Current price: {self.portfolio.currency.upper()} {current_price:.2f} per share")
            print(f"Total invested: {self.portfolio.currency.upper()} {purchase_total_value:.2f}")
            print(f"Current value: {self.portfolio.currency.upper()} {current_total_value:.2f}")
            print(f"Profit/Loss: {self.portfolio.currency.upper()} {profit_loss:+.2f}\n")

            stock_key = stock_name.lower()
            if self.portfolio.asset_exists(stock_key):
                self.portfolio.update_existing_asset(stock_key, stock_amount, current_total_value)
            else:
                stock_asset = Stock(stock_name, stock_amount, current_total_value, self.portfolio.currency.upper(), purchase_price)
                self.portfolio.add_asset(stock_key, stock_asset)
        else:
            print("Could not fetch stock price. Check the ticker name.")

    def adding_assets(self):
        if not self.portfolio.currency:
            currency = input("Type in your desired currency (eur or usd): ").strip().lower()
            self.portfolio.set_currency(currency)

        asset_type = input("Crypto or Stock? ").strip().lower()

        if asset_type == "crypto":
            self.add_crypto()
        elif asset_type == "stock":
            self.add_stock()
        else:
            print("Invalid asset type")

    def edit_portfolio(self):
        if self.portfolio.is_empty():
            print("There are no assets to edit, please add some")
            return

        print("\n-----Current Portfolio-----")
        self.portfolio.display()

        asset_name = input("Enter asset name: ").strip().lower()
        
        if not self.portfolio.asset_exists(asset_name):
            print("Asset not found")
            return
        
        choice = input(f"What do you want to do with {asset_name.capitalize()}?\n1. Change amount\n2. Remove it\n").strip()
        
        if choice == "1":
            new_amount = float(input("Enter new amount: "))
            if self.portfolio.update_asset_amount(asset_name, new_amount):
                print(f"Updated to {new_amount} units")
        elif choice == "2":
            if self.portfolio.remove_asset(asset_name):
                print(f"Removed {asset_name.capitalize()}")
        else:
            print("Invalid choice")

    def run(self):
        while True:
            choice = input("What do you want to do?\n1. To add an asset\n2. View portfolio\n3. To edit or remove an asset\n4. Exit and export your portfolio\n").strip()

            if choice == "1":
                self.adding_assets()
            elif choice == "2":
                if self.portfolio.is_empty():
                    print("Portfolio is empty, please add some assets")
                else:
                    self.portfolio.display()
            elif choice == "3":
                self.edit_portfolio()
            elif choice == "4":
                self.portfolio.export_to_csv()
                break
            else:
                print("Invalid choice, please select 1-4")

class Gui(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.portfolio = Portfolio()
        self.title("Portfolio Tracker")
        self.geometry("1200x700")
        self.configure(bg="#f0f0f0")
        
        self.create_widgets()
        
    def create_widgets(self):
        top_frame = tk.Frame(self, bg="#2c3e50", padx=20, pady=15)
        top_frame.pack(fill=tk.X)
        
        currency_frame = tk.Frame(top_frame, bg="#2c3e50")
        currency_frame.pack(side=tk.LEFT)
        
        tk.Label(currency_frame, text="Currency:", bg="#2c3e50", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.currency_var = tk.StringVar(value="USD")
        currency_combo = ttk.Combobox(currency_frame, textvariable=self.currency_var, values=["USD", "EUR"], state="readonly", width=10)
        currency_combo.pack(side=tk.LEFT, padx=5)
        currency_combo.bind("<<ComboboxSelected>>", self.on_currency_change)
        
        summary_frame = tk.Frame(top_frame, bg="#2c3e50")
        summary_frame.pack(side=tk.RIGHT)
        
        self.total_invested_label = tk.Label(summary_frame, text="Total Invested: $0.00", bg="#2c3e50", fg="white", font=("Arial", 11))
        self.total_invested_label.pack(side=tk.LEFT, padx=15)
        
        self.current_value_label = tk.Label(summary_frame, text="Current Value: $0.00", bg="#2c3e50", fg="white", font=("Arial", 11))
        self.current_value_label.pack(side=tk.LEFT, padx=15)
        
        self.profit_loss_label = tk.Label(summary_frame, text="Profit/Loss: $0.00 (0.00%)", bg="#2c3e50", fg="white", font=("Arial", 11, "bold"))
        self.profit_loss_label.pack(side=tk.LEFT, padx=15)
        
        middle_frame = tk.Frame(self, bg="#f0f0f0")
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        columns = ("Asset", "Type", "Amount", "Purchase Price", "Current Price", "Total Invested", "Current Value", "Profit/Loss")
        self.tree = ttk.Treeview(middle_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=130, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(middle_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        bottom_frame = tk.Frame(self, bg="#f0f0f0", pady=10)
        bottom_frame.pack(fill=tk.X, padx=20, pady=10)
        
        btn_style = {"font": ("Arial", 10, "bold"), "width": 15, "height": 2}
        
        tk.Button(bottom_frame, text="Add Asset", bg="#27ae60", fg="white", command=self.open_add_asset_dialog, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="Edit Asset", bg="#3498db", fg="white", command=self.open_edit_asset_dialog, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="Remove Asset", bg="#e74c3c", fg="white", command=self.remove_asset, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="Refresh Prices", bg="#f39c12", fg="white", command=self.refresh_portfolio, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="Export to CSV", bg="#9b59b6", fg="white", command=self.export_portfolio, **btn_style).pack(side=tk.LEFT, padx=5)
        
        self.portfolio.set_currency(self.currency_var.get())
        
    def on_currency_change(self, event=None):
        currency = self.currency_var.get()
        self.portfolio.set_currency(currency)
        self.refresh_portfolio()
        
    def refresh_portfolio(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if self.portfolio.is_empty():
            self.update_summary(0, 0)
            return
        
        total_current_value = 0
        total_purchase_value = 0
        
        for name, asset in self.portfolio.assets.items():
            if asset.get_type() == "crypto":
                current_price = Crypto.crypto_price(name, self.portfolio.currency)
            else:
                current_price = Stock.stock_price(asset.name, self.portfolio.currency)
            
            if current_price:
                current_value = asset.amount * current_price
                purchase_value = asset.amount * asset.pp_unit
                profit_loss = current_value - purchase_value
                
                self.tree.insert("", tk.END, values=(
                    name.capitalize(),
                    asset.get_type().capitalize(),
                    f"{asset.amount:.4f}",
                    f"{asset.currency} {asset.pp_unit:.2f}",
                    f"{asset.currency} {current_price:.2f}",
                    f"{asset.currency} {purchase_value:.2f}",
                    f"{asset.currency} {current_value:.2f}",
                    f"{asset.currency} {profit_loss:+.2f}"
                ))
                
                total_current_value += current_value
                total_purchase_value += purchase_value
            else:
                current_value = asset.value
                purchase_value = asset.value
                
                self.tree.insert("", tk.END, values=(
                    name.capitalize(),
                    asset.get_type().capitalize(),
                    f"{asset.amount:.4f}",
                    f"{asset.currency} {asset.pp_unit:.2f}",
                    "N/A",
                    f"{asset.currency} {purchase_value:.2f}",
                    f"{asset.currency} {current_value:.2f}",
                    "N/A"
                ))
                
                total_current_value += current_value
                total_purchase_value += purchase_value
        
        self.update_summary(total_purchase_value, total_current_value)
    
    def update_summary(self, total_invested, current_value):
        currency_symbol = "$" if self.currency_var.get() == "USD" else "€"
        
        self.total_invested_label.config(text=f"Total Invested: {currency_symbol}{total_invested:.2f}")
        self.current_value_label.config(text=f"Current Value: {currency_symbol}{current_value:.2f}")
        
        profit_loss = current_value - total_invested
        profit_loss_pct = (profit_loss / total_invested * 100) if total_invested > 0 else 0
        
        color = "#27ae60" if profit_loss >= 0 else "#e74c3c"
        self.profit_loss_label.config(
            text=f"Profit/Loss: {currency_symbol}{profit_loss:+.2f} ({profit_loss_pct:+.2f}%)",
            fg=color
        )
    
    def open_add_asset_dialog(self):
        AddAssetDialog(self, self.portfolio, self.refresh_portfolio)
    
    def open_edit_asset_dialog(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an asset to edit")
            return
        
        item = self.tree.item(selected[0])
        asset_name = item['values'][0].lower()
        
        EditAssetDialog(self, self.portfolio, asset_name, self.refresh_portfolio)
    
    def remove_asset(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an asset to remove")
            return
        
        item = self.tree.item(selected[0])
        asset_name = item['values'][0].lower()
        
        confirm = messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove {asset_name.capitalize()}?")
        if confirm:
            if self.portfolio.remove_asset(asset_name):
                messagebox.showinfo("Success", f"{asset_name.capitalize()} removed successfully")
                self.refresh_portfolio()
    
    def export_portfolio(self):
        if self.portfolio.is_empty():
            messagebox.showwarning("Empty Portfolio", "Portfolio is empty. Please add some assets first.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="portfolio.csv"
        )
        
        if filename:
            if self.portfolio.export_to_csv(filename):
                messagebox.showinfo("Success", f"Portfolio exported to {filename}")
    

class AddAssetDialog(tk.Toplevel):
    def __init__(self, parent, portfolio, refresh_callback):
        super().__init__(parent)
        
        self.portfolio = portfolio
        self.refresh_callback = refresh_callback
        
        self.title("Add Asset")
        self.geometry("500x450")
        self.resizable(False, False)
        self.configure(bg="#ecf0f1")
        
        self.create_widgets()
        
        self.transient(parent)
        self.grab_set()
        
    def create_widgets(self):
        type_frame = tk.LabelFrame(self, text="Asset Type", bg="#ecf0f1", font=("Arial", 10, "bold"), padx=20, pady=10)
        type_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.asset_type_var = tk.StringVar(value="crypto")
        tk.Radiobutton(type_frame, text="Cryptocurrency", variable=self.asset_type_var, value="crypto", bg="#ecf0f1", font=("Arial", 10), command=self.on_type_change).pack(anchor=tk.W, pady=5)
        tk.Radiobutton(type_frame, text="Stock", variable=self.asset_type_var, value="stock", bg="#ecf0f1", font=("Arial", 10), command=self.on_type_change).pack(anchor=tk.W, pady=5)
        
        details_frame = tk.LabelFrame(self, text="Asset Details", bg="#ecf0f1", font=("Arial", 10, "bold"), padx=20, pady=10)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(details_frame, text="Asset Name/Ticker:", bg="#ecf0f1", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = tk.Entry(details_frame, width=30, font=("Arial", 10))
        self.name_entry.grid(row=0, column=1, pady=5, padx=10)
        
        tk.Label(details_frame, text="Amount:", bg="#ecf0f1", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.amount_entry = tk.Entry(details_frame, width=30, font=("Arial", 10))
        self.amount_entry.grid(row=1, column=1, pady=5, padx=10)

        tk.Label(details_frame, text="Purchase Price Method:", bg="#ecf0f1", font=("Arial", 10)).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.price_method_var = tk.StringVar(value="manual")
        price_method_frame = tk.Frame(details_frame, bg="#ecf0f1")
        price_method_frame.grid(row=2, column=1, pady=5, padx=10, sticky=tk.W)
        tk.Radiobutton(price_method_frame, text="Manual", variable=self.price_method_var, value="manual", bg="#ecf0f1", command=self.on_price_method_change).pack(side=tk.LEFT)
        tk.Radiobutton(price_method_frame, text="By Date", variable=self.price_method_var, value="date", bg="#ecf0f1", command=self.on_price_method_change).pack(side=tk.LEFT)
        
        tk.Label(details_frame, text="Purchase Price:", bg="#ecf0f1", font=("Arial", 10)).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.price_entry = tk.Entry(details_frame, width=30, font=("Arial", 10))
        self.price_entry.grid(row=3, column=1, pady=5, padx=10)
        
        tk.Label(details_frame, text="Purchase Date (YYYY-MM-DD):", bg="#ecf0f1", font=("Arial", 10)).grid(row=4, column=0, sticky=tk.W, pady=5)
        self.date_entry = tk.Entry(details_frame, width=30, font=("Arial", 10), state=tk.DISABLED)
        self.date_entry.grid(row=4, column=1, pady=5, padx=10)

        button_frame = tk.Frame(self, bg="#ecf0f1")
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Add Asset", bg="#27ae60", fg="white", font=("Arial", 10, "bold"), width=12, command=self.add_asset).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Cancel", bg="#95a5a6", fg="white", font=("Arial", 10, "bold"), width=12, command=self.destroy).pack(side=tk.LEFT, padx=10)
    
    def on_type_change(self):
        pass
    
    def on_price_method_change(self):
        if self.price_method_var.get() == "manual":
            self.price_entry.config(state=tk.NORMAL)
            self.date_entry.config(state=tk.DISABLED)
        else:
            self.price_entry.config(state=tk.DISABLED)
            self.date_entry.config(state=tk.NORMAL)
    
    def add_asset(self):
        try:
            asset_type = self.asset_type_var.get()
            name = self.name_entry.get().strip().lower()
            amount = float(self.amount_entry.get())
            
            if not name or amount <= 0:
                messagebox.showerror("Invalid Input", "Please enter valid asset name and amount")
                return
            
            if self.price_method_var.get() == "manual":
                purchase_price = float(self.price_entry.get())
            else:
                date = self.date_entry.get().strip()
                if asset_type == "crypto":
                    if name not in Crypto.coin_aliases:
                        messagebox.showerror("Error", f"Unknown crypto: {name}")
                        return
                    coin_id = Crypto.coin_aliases[name]
                    purchase_price = Crypto.crypto_historical_price(coin_id, self.portfolio.currency, date)
                else:
                    purchase_price = Stock.stock_historical_price(name.upper(), self.portfolio.currency, date)
                
                if purchase_price is None:
                    messagebox.showerror("Error", "Could not fetch historical price. Please enter manually.")
                    return

            if asset_type == "crypto":
                if name not in Crypto.coin_aliases:
                    messagebox.showerror("Error", f"Unknown crypto: {name}\nSupported: {', '.join(Crypto.coin_aliases.keys())}")
                    return
                
                coin_id = Crypto.coin_aliases[name]
                current_price = Crypto.crypto_price(coin_id, self.portfolio.currency)
                
                if current_price:
                    current_total_value = amount * current_price
                    crypto_asset = Crypto(coin_id, amount, current_total_value, self.portfolio.currency.upper(), purchase_price)
                    self.portfolio.add_asset(coin_id, crypto_asset)
                    messagebox.showinfo("Success", f"Added {amount} {coin_id.capitalize()}")
                else:
                    messagebox.showerror("Error", "Failed to get current price")
                    return
            else:
                ticker = name.upper()
                current_price = Stock.stock_price(ticker, self.portfolio.currency)
                
                if current_price:
                    current_total_value = amount * current_price
                    stock_asset = Stock(ticker, amount, current_total_value, self.portfolio.currency.upper(), purchase_price)
                    self.portfolio.add_asset(ticker.lower(), stock_asset)
                    messagebox.showinfo("Success", f"Added {amount} shares of {ticker}")
                else:
                    messagebox.showerror("Error", "Failed to get current price. Check ticker symbol.")
                    return
            
            self.refresh_callback()
            self.destroy()
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for amount and price")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")


class EditAssetDialog(tk.Toplevel):
    def __init__(self, parent, portfolio, asset_name, refresh_callback):
        super().__init__(parent)
        
        self.portfolio = portfolio
        self.asset_name = asset_name
        self.refresh_callback = refresh_callback
        
        self.title(f"Edit {asset_name.capitalize()}")
        self.geometry("400x200")
        self.resizable(False, False)
        self.configure(bg="#ecf0f1")
        
        self.create_widgets()

        self.transient(parent)
        self.grab_set()
    
    def create_widgets(self):
        main_frame = tk.Frame(self, bg="#ecf0f1", padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        asset = self.portfolio.assets[self.asset_name]
        
        tk.Label(main_frame, text=f"Current Amount: {asset.amount}", bg="#ecf0f1", font=("Arial", 10)).pack(pady=10)
        
        tk.Label(main_frame, text="New Amount:", bg="#ecf0f1", font=("Arial", 10)).pack(pady=5)
        self.new_amount_entry = tk.Entry(main_frame, width=30, font=("Arial", 10))
        self.new_amount_entry.insert(0, str(asset.amount))
        self.new_amount_entry.pack(pady=5)
        
        button_frame = tk.Frame(main_frame, bg="#ecf0f1")
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Update", bg="#3498db", fg="white", font=("Arial", 10, "bold"), width=12, command=self.update_asset).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Cancel", bg="#95a5a6", fg="white", font=("Arial", 10, "bold"), width=12, command=self.destroy).pack(side=tk.LEFT, padx=10)
    
    def update_asset(self):
        try:
            new_amount = float(self.new_amount_entry.get())
            if new_amount <= 0:
                messagebox.showerror("Invalid Input", "Amount must be greater than 0")
                return
            
            if self.portfolio.update_asset_amount(self.asset_name, new_amount):
                messagebox.showinfo("Success", f"Updated {self.asset_name.capitalize()} to {new_amount} units")
                self.refresh_callback()
                self.destroy()
            else:
                messagebox.showerror("Error", "Failed to update asset")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number")

if __name__ == "__main__":
    app = Gui()
    app.mainloop()