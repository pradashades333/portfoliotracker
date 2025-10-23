import yfinance as yf
import requests
import pandas as pd
from datetime import datetime

class Asset:
    def __init__(self, name, amount, value, currency, pp_unit ):
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
            "pp unit": self.pp_unit
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
        url_coingecko = "https://api.coingecko.com/api/v3/simple/price"
        params = {'ids': coin_id, 'vs_currencies': currency}
        response = requests.get(url_coingecko, params=params)

        if response.status_code == 200:
            data = response.json()
            return data[coin_id][currency]
        else:
            return None
    
    @staticmethod
    def crypto_time(coin_id, currency, date):
        try:

            date = datetime.strptime(date, "%Y-%m-%d")
            date_format = date.strftime(("%d-%m-%Y"))

            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/history"
            params = {'date':date_format}
            response = requests.get(url, params = params)

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
        
    @staticmethod
    def stock_time(stock_name, currency, date):
        try:
            stock = yf.Ticker(stock_name)
            hist = stock.history(start = date, end  = date)

            if hist.empty:
                return None
            
            stock_price_usd = hist['Close'].iloc[0]
            if currency.upper() == "USD":
                return stock_price_usd

            
            forex_pair = f"{currency.upper()}USD=X"
            forex = yf.Ticker(forex_pair)
            forex_time = forex.history(start=date, end=date)

            if not forex_time.empty:
                exchange_rate = forex_time['Close'].iloc[0]
                return stock_price_usd / exchange_rate
            else:
                return None
        except Exception as e:
            print(f"Error fetching historical stock price: {e}")
            return None


            
    

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
        
        total_value = 0
        print("-------PORTFOLIO TOTAL:------\n")

        for name, asset in self.assets.items():
            print(f"{name.capitalize()} ({asset.get_type()}): {asset.amount} units = {asset.currency} {asset.value:.2f}")
            total_value += asset.value

        print(f"\nTotal Portfolio Value: {asset.currency} {total_value:.2f}\n")

    def export_to_csv(self, filename="portfolio.csv"):
        if not self.assets:
            print("Portfolio is empty, please add some assets")
            return
        else:
            df = pd.DataFrame([
                {
                    "Asset Name": name,
                    "Type of Asset": asset.get_type(),
                    "Amount": asset.amount,
                    "Total Value": asset.value,
                    "Currency": asset.currency
                }
                for name, asset in self.assets.items()
            ])

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
            price = Crypto.crypto_price(coin_id, self.portfolio.currency)

            if price:
                total_value = crypto_amount * price
                print(f"Added {crypto_amount} {coin_id.capitalize()} with the price of {self.portfolio.currency.upper()} {total_value} to portfolio")

                crypto_asset = Crypto(coin_id, crypto_amount, total_value, self.portfolio.currency.upper())
                self.portfolio.add_asset(coin_id, crypto_asset)
            else:
                print("Failed to get price")
        else:
            print("Unknown crypto, check the name or type another one")

    def add_stock(self):
        print("You selected stock:")
        stock_name = input("Type the stock ticker: ").upper()
        stock_amount = float(input(f"How much of {stock_name} do you own? "))
        
        price = Stock.stock_price(stock_name, self.portfolio.currency)

        if price:
            total_value = stock_amount * price
            print(f"{stock_amount} shares of {stock_name} = {self.portfolio.currency.upper()} {total_value:.2f}")

            stock_key = stock_name.lower()
            if self.portfolio.asset_exists(stock_key):
                self.portfolio.update_existing_asset(stock_key, stock_amount, total_value)
            else:
                stock_asset = Stock(stock_name, stock_amount, total_value, self.portfolio.currency.upper())
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


if __name__ == "__main__":
    app = PortfolioApp()
    app.run()