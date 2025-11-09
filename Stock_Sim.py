#TERMINAL STOCK SIM -------
import random
import json
import os
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np
import threading
import time
from cryptography.fernet import Fernet
import base64
import hashlib
import select
import math
import sys, time, random, tty, termios, select


SAVE_FILE = "stock_save.json"

# =========================
# 🔐 Encryption System
# =========================
def get_encryption_key():
    secret_passphrase = "SusBus420204569"
    key = hashlib.sha256(secret_passphrase.encode()).digest()
    return base64.urlsafe_b64encode(key[:32])


def encrypt_data(data: str) -> bytes:
    f = Fernet(get_encryption_key())
    return f.encrypt(data.encode())


def decrypt_data(encrypted: bytes) -> str:
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted).decode()

# --- Game Setup ---
balance = 5000.0
bank_balance = 0.0
bank_interest_rate = 0.0
bank_interest_cost = 10000.0
portfolio = {}
shorts = {}
price_history = {}
trade_history = []
current_page = 0
STOCKS_PER_PAGE = 10
play_mode = False
days_passed = 0
AUTO_SAVE_INTERVAL = 5 
last_auto_save_day = 0
day = 1
next_interest_day = 7
mode = "Normal"
insider_predictions = {}  
INSIDER_INFO_COST = 10000  
black_market_history = []
FAST_FORWARD_COOLDOWN_DAYS = 7   
last_fast_forward_day = None     
FAKE_ID_LOCK_DAYS = 95
fake_id_locked_until = 0
vegas_jackpot = 25000.0  # base jackpot value
NEW_GAME_FLAG = False


# --- NEW: per-stock supply mapping ---
stock_supply = {}  # mapping stock -> total available supply (int)

# --- GBM Parameters ---
DAILY_DRIFT = 0.0005
DAILY_VOLATILITY = 0.02

# --- DLC Setup ---
dlc_packs = {
    "Tech Titans DLC": {"stocks": ["AURORA", "CYBRX", "VANTEX", "SOLIX", "MEGADATA"], "price": 4200.69},
    "Elon DLC": {"stocks": ["SPACEX", "XCORP", "BORINGCO", "NEURALINK", "PAYPAL"], "price": 6969.69},
    "Fanchise Fusion Force DLC": {"stocks": ["SOA", "MTG", "POKEMON", "SPONGEBOB", "LOSPOLLOS","KRUSTYK","MINECRAFT","WONKA","DUFF","UMBRELLA","WAYNE","INITECH"], "price": 9999.69},
    "Energy Evolution DLC": {"stocks": ["SUNW", "HYDRX", "GEOCORP", "NUCLEARA", "WINDO"], "price": 15000.50},
    "Crypto Chaos DLC": {"stocks": ["BITMAX", "DOGX", "ETHRZ", "COINLY", "SOLPRO"], "price": 52000.00},
    "Luxury Legends DLC": {"stocks": ["PRADA", "ROLEX", "TESORO", "DIORX", "MCLRN"], "price": 69000.99},
    "AI Uprising DLC": {"stocks": ["SYNTHIX", "QUANTIA", "NEURONIX", "BOTCORP", "CYNET"], "price": 77777.77},
    "Sus Bus DLC": {"stocks": ["DASUSBUS", "MORESUS", "XSdUSX", "2045", "SUSCOIN","MOREBUS","BIGSUS","LILSUS","MEGASUS","SMALLSUS"], "price": 42069.99},
    "MEME DLC": {"stocks": ["OVR9000", "80085", "AMUNGUS", "TRUMPCOIN", "PEPE","DOGECOIN","FARTCOIN","GIGACHAD","TOTHEMOON","AVOCADO"], "price": 123456.78}
}

purchased_dlcs = []
locked_dlc_stocks = {dlc: data["stocks"][:] for dlc, data in dlc_packs.items()}

# track which DLC stocks have been unlocked (names)
dlc_stocks_unlocked = []

def is_dlc_locked(stock_name):
    """Check if a stock belongs to an unpurchased DLC."""
    for dlc_name, stock_list in locked_dlc_stocks.items():
        if stock_name in stock_list and dlc_name not in purchased_dlcs:
            return True
    return False

if "vegas_stats" not in globals():
    vegas_stats = {
        "slots_played": 0,
        "blackjack_wins": 0,
        "blackjack_losses": 0,
        "roulette_bets": 0,
        "jackpots_won": 0,
        "games_played": 0,
        "total_bets": 0.0,
        "total_won": 0.0,
        "total_lost": 0.0,
        "net": 0.0
    }


# --- Stock Generation ---
def generate_stocks():
    """Return a dict mapping stock symbol -> starting price (float)."""
    stock_names = [
        "AAPL","GOOG","AMZN","TSLA","META","NFLX","NVDA","AMD","MSFT","INTC",
        "BABA","ORCL","XOM","CVX","KO","PEP","DIS","NKE","V","MA",
        "JPM","WMT","PFE","MRNA","SONY","BA","UBER","LYFT","COST","IBM",
        "SHOP","SQ","ADBE","CRM","PYPL","T","VZ","BP","RBLX","EA",
        "TTWO","PLTR","UBS","SPOT","FORD","GM","CSCO","ABNB","RIVN","SOFI",
        "TWTR","SNAP","ZM","DOCU","ROKU","CRWD","FSLY","OKTA","NET","DDOG",
        "SNOW","BYND","MELI","SE","WIX","ETSY","TEAM","ZEN","COIN",
        "AMC","GME","SPCE","DKNG","PLUG","NIO","LI","XPEV","BIDU","JD",
        "IQ","CHWY","TSM","ASML","INTU","ADSK","TTD","SUS","SUSBUS","X","DIAMOND",
        "GOLD","SILVER","IRON","STRK","MEMECOIN"
    ]
    random.shuffle(stock_names)
    selected = stock_names[:109]
    new_stocks = {name: round(random.uniform(0.3, 1250.0), 2) for name in selected}
    return new_stocks
    
# --- Black Market System ---

# --- Fake ID system for Black Market ---
FAKE_ID_BASE_COST = 15000.0
FAKE_ID_COST = FAKE_ID_BASE_COST   # current price (increases when confiscated OR purchased)
player_has_fake_id = False         # whether the player currently has a valid fake id

# Multipliers:
FAKE_ID_COST_INCREASE = 1.25       # used when ID is confiscated (existing behavior)
FAKE_ID_PURCHASE_INCREASE = 1.15   # NEW: price increases 15% after each purchase



BLACK_MARKET_ITEMS = {
    "Forged Misle 🚀": {"price": 1250000.0, "risk": 0.65, "days": 30},
    "Passports 🪪": {"price": 1000.0, "risk": 0.07, "days": 5},
    "Cedit Cards 💳": {"price": 850.0, "risk": 0.07, "days": 5},
    "Handgun /̵͇̿̿/'̿'̿ ̿ ̿̿  ": {"price": 4000.0, "risk": 0.20, "days": 10},
    "Stimulants Pack 💊": {"price": 2500.0, "risk": 0.25, "days": 10},
    "Luxury Knockoffs ⌚ 💍 👑": {"price": 900.0, "risk": 0.10, "days": 10},
    "Rifle ▄︻╦芫≡══-- ": {"price": 12000.0, "risk": 0.28, "days": 10},
    "Rifle box ▄︻╦芫≡══-- 📦": {"price": 120000.0, "risk": 0.50, "days": 10},
    "Ak-47 ⌐╦ᡁ᠊╾━": {"price": 15000.0, "risk": 0.28, "days": 10},
    "Ak-47 box ⌐╦ᡁ᠊╾━ 📦": {"price": 150000.0, "risk": 0.50, "days": 10},
    "M4 ᡕᠵデ气亠": {"price": 25000.0, "risk": 0.35, "days": 10},
    "M4 box ᡕᠵデ气亠 📦": {"price": 250000.0, "risk": 0.50, "days": 10},
    "Handgun Ammo ✏📦": {"price": 3500.0, "risk": 0.15, "days": 10},
    "Rilfe Ammo ✏📦": {"price": 4000.0, "risk": 0.15, "days": 10},
    "Ak-47 Ammo ✏📦": {"price": 4500.0, "risk": 0.15, "days": 10},
    "M4 Ammo ✏📦": {"price": 5000.0, "risk": 0.15, "days": 10},
    "Weed - 10 lbs 🌿🚬": {"price": 45000.0, "risk": 0.25, "days": 10},
    "LSD - 5 oz 🌌🌅": {"price": 18000.0, "risk": 0.15, "days": 20},
    "Cocaine - 10 Bricks 🍚": {"price": 65000.0, "risk": 0.35, "days": 25},
    "Meth - 20 lbs 🧪🧊": {"price": 70000.0, "risk": 0.35, "days": 15},
    
}

# Player holdings of black market goods: { item_name: qty }
black_market_inventory = {}

# Active sale orders: list of dicts:
# { "item": name, "qty": int, "price_per_unit": float, "days_left": int, "confiscation_risk": float }
black_market_orders = []

# Fixed sale multiplier (350% return = 3.5x)
BLACK_MARKET_SALE_MULTIPLIER = 3.5

# Fulfillment time in days
BLACK_MARKET_FULFILL_DAYS = 10

# Default confiscation check at fulfillment (we will use each item's risk)
# (Note: items also store a 'risk' baseline; you can multiply or adjust if you like)

# --- Heist system -- fictional minigames only ---
HEIST_EQUIPMENT = {
    "Fake ID": {"price": 15000.0},
    "Passport": {"price": 8000.0},
    "Credit Card (cloned)": {"price": 5000.0},
    "Drill": {"price": 3000.0},
    "Spare Drill Bit": {"price": 3000.0},
    "Hacking Software": {"price": 7500.0},
    "Hacking LapTop": {"price": 9250.0},
    "Guard uniform": {"price": 500.0},
    "Get Away Car": {"price": 25000.0},
    "Inside Man Fee": {"price": 10000.0}
}

heist_inventory = {}   # player's owned heist-specific gear (can share black_market_inventory if you prefer)
heist_wanted_flags = []  # list of dicts: { "type": "bank"|"hacking", "days_left": int, "daily_catch_p": float, "total_catch": float, "created_day": int }
heist_history = []     # record of completed/failed heists
HEIST_WANTED_DAYS = 60
HEIST_CATCH_PROB_TOTAL = 0.30  # 30% chance across the window


def generate_stock_history(current_price, days=60):
    prices = []
    S = current_price
    for _ in range(days):
        Z = np.random.normal()
        S = S * np.exp((DAILY_DRIFT - 0.5 * DAILY_VOLATILITY**2) + DAILY_VOLATILITY * Z)
        S = max(0.01, S)
        prices.append(round(S, 2))
    return prices

def generate_dlc_stocks(stock_list):
    """Generate special DLC stocks that are more stable but can still crash.
       Returns a dict mapping stock_name -> price (float). Also fills price_history and stock_supply.
    """
    dlc_stocks = {}
    for name in stock_list:
        price = round(random.uniform(25, 600.0), 2)
        dlc_stocks[name] = price
        # assign supply for DLC stocks too
        stock_supply[name] = random.randint(100, 100000)
        days = random.randint(40, 90)
        prices = []
        S = price
        for _ in range(days):
            Z = np.random.normal()
            S = S * np.exp((DAILY_DRIFT * 1.5 - 0.5 * (DAILY_VOLATILITY * 0.6)**2) + (DAILY_VOLATILITY * 0.6) * Z)
            S = max(0.01, S)
            prices.append(round(S, 2))
        price_history[name] = prices
    return dlc_stocks

def add_dlc_stocks_to_market(dlc_name):
    """Unlock DLC stocks and add them to market."""
    global stocks, dlc_stocks_unlocked
    if dlc_name not in dlc_packs:
        print(f"⚠️ Unknown DLC: {dlc_name}")
        return
    stock_list = dlc_packs[dlc_name]["stocks"]
    new_stocks = generate_dlc_stocks(stock_list)
    stocks.update(new_stocks)
    dlc_stocks_unlocked.extend(list(new_stocks.keys()))
    print(f"🆕 Added {len(new_stocks)} new stocks from {dlc_name}!")
    
def buy_dlc():
    global balance, stocks
    print("\n=== 🧩 DLC Market ===")
    for i, (dlc_name, dlc_info) in enumerate(dlc_packs.items(), 1):
        owned = "✅ Purchased" if dlc_name in purchased_dlcs else f"💲 ${dlc_info['price']:.2f}"
        print(f"{i}) {dlc_name} ({len(dlc_info['stocks'])} stocks) - {owned}")

    choice = input("\nEnter DLC number to buy or press Enter to cancel: ")
    if not choice:
        return
    try:
        idx = int(choice)
        dlc_name = list(dlc_packs.keys())[idx - 1]
    except (ValueError, IndexError):
        print("Invalid choice.")
        return

    dlc_info = dlc_packs[dlc_name]
    price = dlc_info["price"]

    if dlc_name in purchased_dlcs:
        print(f"You already own {dlc_name}.")
        return
    if balance < price:
        print(f"Not enough cash! {dlc_name} costs ${price:.2f}")
        return

    balance -= price
    purchased_dlcs.append(dlc_name)

    # Unlock DLC stocks (this will update `stocks`, `price_history`, `stock_supply`)
    stock_list = dlc_info["stocks"]
    add_dlc_stocks_to_market(dlc_name)

    # Print added stock names (list)
    print(f"\n🎉 You purchased {dlc_name} for ${price:.2f}! Added new premium stocks!")
    print("  🆕" + ", ".join(stock_list))

# --- Initialize base market at module load ---
stocks = generate_stocks()
for s in list(stocks.keys()):
    # random supply between 10,000 and 1,000,000 shares
    stock_supply[s] = random.randint(10000, 1000000)
for s, price in stocks.items():
    days = random.randint(30, 100)
    price_history[s] = generate_stock_history(price, days)

def format_money(value):
    """Formats numbers with commas and 2 decimal places."""
    return f"${value:,.2f}"

# --- Display ---
def print_stocks(page=0):
    """Show only base game and purchased DLC stocks with 60-day performance and market summary."""
    unlocked_stocks = {name: price for name, price in stocks.items() if not is_dlc_locked(name)}
    stock_list = list(unlocked_stocks.items())
    start = page * STOCKS_PER_PAGE
    end = start + STOCKS_PER_PAGE
    page_stocks = stock_list[start:end]

    # --- Calculate overall market performance (market cap using supply) ---
    total_market_cap_now = 0.0
    total_market_cap_old = 0.0
    count = 0
    for name, price in unlocked_stocks.items():
        supply = stock_supply.get(name, 0)
        if name in price_history and len(price_history[name]) > 1 and supply > 0:
            old_price = price_history[name][-60] if len(price_history[name]) >= 60 else price_history[name][0]
            total_market_cap_now += price * supply
            total_market_cap_old += old_price * supply
            count += 1

    market_change = ((total_market_cap_now - total_market_cap_old) / total_market_cap_old) * 100 if total_market_cap_old > 0 else 0

    # --- Display overall market summary ---
    arrow = "📈" if market_change > 0 else ("📉" if market_change < 0 else "➖")
    color = "\033[92m" if market_change > 0 else ("\033[91m" if market_change < 0 else "\033[0m")
    print("\n=== 🏦 Market Overview ===")
    print(f"Market Trend (60d, by market cap): {color}{arrow} {market_change:+.2f}%\033[0m")
    print(f"Total Market Value (unlocked market cap): ${total_market_cap_now:,.2f}")
    print("=========================")

    # --- Show stock list ---
    total_pages = max(1, (len(stock_list) - 1)//STOCKS_PER_PAGE + 1)
    print(f"\n📊 Available Stocks (Page {page + 1}/{total_pages})")
    print("Name       |   Price ($)   |  Supply   |  60d Change | Own All  ✅️")
    print("------------------------------------------------------------------")

    for name, price in page_stocks:
        supply = stock_supply.get(name, 0)
        owned_qty = portfolio.get(name, {}).get("qty", 0.0)
        owns_all = owned_qty >= supply and supply > 0
        owned_marker = "✅" if owns_all else (" " if owned_qty > 0 else " ")
        if name in price_history and len(price_history[name]) > 1:
            old_price = price_history[name][-60] if len(price_history[name]) >= 60 else price_history[name][0]
            change_pct = ((price - old_price) / old_price) * 100 if old_price > 0 else 0
            arrow = "📈" if change_pct > 0 else ("📉" if change_pct < 0 else "➖")
            color = "\033[92m" if change_pct > 0 else ("\033[91m" if change_pct < 0 else "\033[0m")
            display_name = f"{name}{' 🧩' if name in dlc_stocks_unlocked else ''}"
            print(f"{display_name:<11} | ${price:<10.2f} | {supply:>7}   | {color}{arrow} {change_pct:+6.2f}%\033[0m | {owned_marker}")
        else:
            display_name = f"{name}{' 🧩' if name in dlc_stocks_unlocked else ''}"
            print(f"{display_name:<11} | ${price:<10.2f} | {supply:>7}   | (no data)    | {owned_marker}")

    print("------------------------------------------------------------------")

def show_all():
    """Show all unlocked (base + purchased DLC) stocks with 60-day % change and supply/owned-all marker."""
    visible_stocks = {name: price for name, price in stocks.items() if not is_dlc_locked(name)}
    print("\n=== 📊 All Unlocked Stocks (with 60-Day Change) ===")
    print("Name       |   Price ($)   |  Supply   |  60d Change | Own All  ✅️")
    print("------------------------------------------------------------------")
    for name, price in sorted(visible_stocks.items()):
        supply = stock_supply.get(name, 0)
        owned_qty = portfolio.get(name, {}).get("qty", 0.0)
        owns_all = owned_qty >= supply and supply > 0
        owned_marker = "✅" if owns_all else (" " if owned_qty > 0 else " ")
        if name in price_history and len(price_history[name]) > 1:
            old_price = price_history[name][-60] if len(price_history[name]) >= 60 else price_history[name][0]
            change_pct = ((price - old_price) / old_price) * 100 if old_price > 0 else 0
            arrow = "📈" if change_pct > 0 else ("📉" if change_pct < 0 else "➖")
            color = "\033[92m" if change_pct > 0 else ("\033[91m" if change_pct < 0 else "\033[0m")
            display_name = f"{name}{' 🧩' if name in dlc_stocks_unlocked else ''}"
            print(f"{display_name:<11} | ${price:<10.2f} | {supply:>7}   | {color}{arrow} {change_pct:+6.2f}%\033[0m | {owned_marker}")
        else:
            display_name = f"{name}{' 🧩' if name in dlc_stocks_unlocked else ''}"
            print(f"{display_name:<11} | ${price:<10.2f} | {supply:>7}   | (no data)    | {owned_marker}")
    print("------------------------------------------------------------------")

def print_portfolio():
    print("\n=== 💼 Portfolio 💼 ===")
    print(f" 🗓️  Day: {days_passed}")
    total_value = balance + bank_balance
    if not portfolio:
        print("You have no holdings.")
    for name, data in portfolio.items():
        qty = data["qty"]
        avg_price = data["avg_price"]
        current_price = stocks.get(name, 0.0)
        stock_value = qty * current_price
        change_pct = ((current_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0
        total_value += stock_value
        print(f"{name}: {qty:.3f} shares | Value: ${stock_value:.2f} | Gain/Loss: {change_pct:.2f}%")
    for name, short in shorts.items():
        short_value = short["shares"] * (short["sell_price"] - stocks.get(name, 0.0))
        change_pct = ((short["sell_price"] - stocks.get(name, 0.0)) / short["sell_price"]) * 100 if short["sell_price"] > 0 else 0
        total_value += short_value
        print(f"{name} (SHORT): {short['shares']:.3f} shares | P/L: ${short_value:.2f} | Gain/Loss: {change_pct:.2f}%")
    print()
    print(f"💰  Cash: {format_money(balance)}")
    print(f"🏛️  Bank: {format_money(bank_balance)}")
    print(f"📈 Bank Interest: {bank_interest_rate*100:.3f}% | Upgrade Cost: ${bank_interest_cost:.2f}")
    print(f"💲 Total Value: {format_money(total_value)}")
    print("=========================")

def show_trade_history():
    print("\n=== Trade History (last 100 trades) ===")
    if not trade_history:
        print("No trades yet.")
        return
    for entry in trade_history[-100:]:
        print(entry)
    print("=========================")

# --- Core ---
def log_trade(action, stock, qty, price, result=None):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {action.upper()} {qty:.3f}x {stock} @ ${price:.2f}"
    if result:
        entry += f" | Result: {result}"
    trade_history.append(entry)

def update_stocks():
    global days_passed, bank_balance
    for name in list(stocks.keys()):
        S = stocks[name]
        Z = np.random.normal()
        S_new = S * np.exp((DAILY_DRIFT - 0.5 * DAILY_VOLATILITY**2) + DAILY_VOLATILITY * Z)
        stocks[name] = round(max(0.01, S_new), 2)
        # ensure price_history list exists
        price_history.setdefault(name, []).append(stocks[name])
    if bank_balance > 0 and bank_interest_rate > 0:
        # NOTE: weekly interest handled separately; this is not applied here
        pass
    days_passed += 1

def show_graph(stock):
    global play_mode
    stock = stock.upper()
    if stock not in price_history:
        print("Invalid stock.")
        return

    was_playing = play_mode
    play_mode = False
    print("\n📈 Generating candlestick chart window... (close it to continue)")
    print_stocks(current_page)
    print_portfolio()

    try:
        last_60 = price_history[stock][-60:]
        if len(last_60) < 2:
            print("Not enough data to render candlesticks.")
            return

        ohlc = []
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=len(last_60) - 1)
        for i, close_price in enumerate(last_60):
            date = start_date + datetime.timedelta(days=i)
            date_num = mdates.date2num(date)
            open_price = last_60[i - 1] if i > 0 else close_price
            wiggle_pct = random.uniform(0.002, 0.03)
            high = max(open_price, close_price) * (1 + random.uniform(0.0, wiggle_pct))
            low = min(open_price, close_price) * (1 - random.uniform(0.0, wiggle_pct))
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            if low <= 0:
                low = 0.01
            ohlc.append([date_num, float(round(open_price, 4)), float(round(high, 4)), float(round(low, 4)), float(round(close_price, 4))])

        fig, ax = plt.subplots(figsize=(10, 5))
        width = 0.6
        for date_num, open_p, high, low, close_p in ohlc:
            color = 'green' if close_p >= open_p else 'red'
            ax.plot([date_num, date_num], [low, high], color='black', linewidth=1)
            lower = min(open_p, close_p)
            height = abs(close_p - open_p)
            if height == 0:
                height = (high - low) * 0.001 if (high - low) > 0 else 0.0001
            rect = Rectangle((date_num - width/2, lower), width, height, facecolor=color, edgecolor='black', alpha=0.85)
            ax.add_patch(rect)

        ax.xaxis_date()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.set_title(f"{stock} Price History (Last {len(last_60)} Days) - Candlesticks")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price ($)")
        plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
        plt.grid(True)
        plt.tight_layout()
        plt.show()
        plt.close()
    except Exception as e:
        print(f"⚠️ Graph error: {e}")
    finally:
        play_mode = was_playing
    print_stocks(current_page)
    print_portfolio()

def show_market_graph():
    global play_mode
    unlocked = {name: hist for name, hist in price_history.items() if name in stocks and not is_dlc_locked(name)}
    if not unlocked:
        print("No unlocked stocks with history to build market graph.")
        return
    max_len = max(len(hist) for hist in unlocked.values())
    L = min(60, max_len)
    market_history = []
    for offset in range(-L, 0):
        day_values = []
        for hist in unlocked.values():
            if len(hist) >= abs(offset):
                day_values.append(hist[offset])
        if day_values:
            market_history.append(round(float(np.mean(day_values)), 4))
    if len(market_history) < 2:
        print("Not enough aggregated market data to render chart.")
        return

    was_playing = play_mode
    play_mode = False
    print("\n📈 Generating MARKET candlestick chart window... (close it to continue)")
    print_stocks(current_page)
    print_portfolio()

    try:
        last_60 = market_history
        ohlc = []
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=len(last_60) - 1)
        for i, close_price in enumerate(last_60):
            date = start_date + datetime.timedelta(days=i)
            date_num = mdates.date2num(date)
            open_price = last_60[i - 1] if i > 0 else close_price
            wiggle_pct = random.uniform(0.002, 0.02)
            high = max(open_price, close_price) * (1 + random.uniform(0.0, wiggle_pct))
            low = min(open_price, close_price) * (1 - random.uniform(0.0, wiggle_pct))
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            if low <= 0:
                low = 0.01
            ohlc.append([date_num, float(round(open_price, 4)), float(round(high, 4)), float(round(low, 4)), float(round(close_price, 4))])

        fig, ax = plt.subplots(figsize=(12, 6))
        width = 0.6
        for date_num, open_p, high, low, close_p in ohlc:
            color = 'green' if close_p >= open_p else 'red'
            ax.plot([date_num, date_num], [low, high], color='black', linewidth=1)
            lower = min(open_p, close_p)
            height = abs(close_p - open_p)
            if height == 0:
                height = (high - low) * 0.001 if (high - low) > 0 else 0.0001
            rect = Rectangle((date_num - width/2, lower), width, height, facecolor=color, edgecolor='black', alpha=0.85)
            ax.add_patch(rect)

        ax.xaxis_date()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.set_title(f"MARKET Index (Aggregated Average Close) - Last {len(last_60)} Days")
        ax.set_xlabel("Date")
        ax.set_ylabel("Index Value")
        plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
        plt.grid(True)
        plt.tight_layout()
        plt.show()
        plt.close()
    except Exception as e:
        print(f"⚠️ Market graph error: {e}")
    finally:
        play_mode = was_playing

# --- Trading ---
def buy_stock():
    global balance
    stock = input("Enter stock name to buy: ").upper()
    if stock not in stocks:
        print("Invalid stock.")
        return
    try:
        qty = float(input("Enter quantity to buy (fractional ok): "))
    except ValueError:
        print("Invalid quantity.")
        return
    if qty <= 0:
        print("Enter a positive quantity.")
        return

    supply = stock_supply.get(stock, 0)
    owned_qty = portfolio.get(stock, {}).get("qty", 0.0)
    available_to_buy = max(0.0, supply - owned_qty)

    if qty > available_to_buy:
        print(f"Not enough supply available. Supply: {supply}, You own: {owned_qty:.3f}. Available to buy: {available_to_buy:.3f}")
        return

    cost = qty * stocks[stock]
    if cost > balance:
        print("Not enough funds!")
        return
    balance -= cost
    if stock in portfolio:
        total_qty = portfolio[stock]["qty"] + qty
        avg_price = ((portfolio[stock]["avg_price"] * portfolio[stock]["qty"]) + cost) / total_qty
        portfolio[stock]["qty"] = total_qty
        portfolio[stock]["avg_price"] = avg_price
    else:
        portfolio[stock] = {"qty": qty, "avg_price": stocks[stock]}
    print(f"Bought {qty:.3f} of {stock}")
    log_trade("BUY", stock, qty, stocks[stock])

def sell_stock():
    global balance
    if not portfolio:
        print("You don’t own any stocks.")
        return
    print("\n1) Sell Specific Stock\n2) Sell All Stocks")
    choice = input("Choose option: ")
    if choice == "2":
        sell_all()
        return
    stock = input("Enter stock name to sell: ").upper()
    if stock not in portfolio:
        print("You don’t own that stock.")
        return

    sub_choice = input(f"Sell all {stock}? (y/n): ").lower()
    if sub_choice == "y":
        qty = portfolio[stock]["qty"]
    else:
        try:
            qty = float(input("Enter quantity to sell (fractional ok): "))
        except ValueError:
            print("Invalid quantity.")
            return
        if qty > portfolio[stock]["qty"]:
            print("Not enough shares.")
            return

    avg_price = portfolio[stock]["avg_price"]
    gain_loss = qty * (stocks[stock] - avg_price)  # profit/loss
    balance += qty * stocks[stock]
    portfolio[stock]["qty"] -= qty
    if portfolio[stock]["qty"] <= 0:
        del portfolio[stock]

    print(f"Sold {qty:.3f} of {stock} | P/L: ${gain_loss:.2f}")
    log_trade("SELL", stock, qty, stocks[stock], result=f"P/L ${gain_loss:.2f}")

    # --- Refresh display after selling ---
    print_stocks(current_page)
    print_portfolio()

def sell_all():
    global balance
    if not portfolio:
        print("You don’t own any stocks.")
        return
    total_proceeds = 0
    for stock, data in list(portfolio.items()):
        qty = data["qty"]
        avg_price = data["avg_price"]
        gain_loss = qty * (stocks[stock] - avg_price)
        proceeds = qty * stocks[stock]
        balance += proceeds
        total_proceeds += proceeds
        log_trade("SELL", stock, qty, stocks[stock], result=f"P/L ${gain_loss:.2f}")
        print(f"Sold all {qty:.3f} of {stock} | P/L: ${gain_loss:.2f}")
        del portfolio[stock]
    print(f"\n💰 Sold all holdings | Total proceeds: ${total_proceeds:.2f}")

    # Refresh display
    print_stocks(current_page)
    print_portfolio()

def short_stock():
    global balance
    stock = input("Enter stock to short: ").upper()
    if stock not in stocks:
        print("Invalid stock.")
        return
    try:
        qty = float(input("Enter quantity to short (fractional ok): "))
    except ValueError:
        print("Invalid quantity.")
        return
    cost_to_short = qty * stocks[stock]
    if cost_to_short > balance:
        print("Not enough cash to short that much!")
        return
    balance -= cost_to_short
    if stock in shorts:
        shorts[stock]["shares"] += qty
    else:
        shorts[stock] = {"shares": qty, "sell_price": stocks[stock]}
    print(f"Shorted {qty:.3f} {stock} using ${cost_to_short:.2f} margin.")
    log_trade("SHORT", stock, qty, stocks[stock])

def cover_all():
    global balance
    if not shorts:
        print("No short positions to cover.")
        return
    total_pl = 0
    for stock, data in list(shorts.items()):
        qty = data["shares"]
        profit = (data["sell_price"] - stocks[stock]) * qty
        balance += profit + (data["sell_price"] * qty)
        total_pl += profit
        log_trade("COVER", stock, qty, stocks[stock], result=f"P/L ${profit:.2f}")
        print(f"Covered all {qty:.3f} of {stock}, P/L: ${profit:.2f}")
        del shorts[stock]
    print(f"\n📉 Covered all shorts | Total P/L: ${total_pl:.2f}")

def cover_short():
    global balance
    if not shorts:
        print("You have no short positions.")
        return
    print("\n1) Cover Specific Short\n2) Cover All Shorts")
    choice = input("Choose option: ")
    if choice == "2":
        cover_all()
        return
    stock = input("Enter stock to cover: ").upper()
    if stock not in shorts:
        print("You have no short position in that stock.")
        return

    sub_choice = input(f"Cover all {stock}? (y/n): ").lower()
    if sub_choice == "y":
        qty = shorts[stock]["shares"]
    else:
        try:
            qty = float(input("Enter quantity to cover (fractional ok): "))
        except ValueError:
            print("Invalid quantity.")
            return
        if qty > shorts[stock]["shares"]:
            print("Not that many shares shorted.")
            return

    profit = (shorts[stock]["sell_price"] - stocks[stock]) * qty
    balance += profit + (shorts[stock]["sell_price"] * qty)
    shorts[stock]["shares"] -= qty
    print(f"Covered {qty:.3f} of {stock}, P/L: ${profit:.2f}")
    log_trade("COVER", stock, qty, stocks[stock], result=f"P/L ${profit:.2f}")
    if shorts[stock]["shares"] <= 0:
        del shorts[stock]

# --- Bank ---
def deposit_bank():
    global balance, bank_balance
    try:
        amt = float(input("Enter deposit amount: "))
    except ValueError:
        print("Invalid amount.")
        return
    if amt > balance:
        print("Not enough cash.")
        return
    balance -= amt
    bank_balance += amt
    print(f"Deposited ${amt:.2f}")

def withdraw_bank():
    global balance, bank_balance
    try:
        amt = float(input("Enter withdraw amount: "))
    except ValueError:
        print("Invalid amount.")
        return
    if amt > bank_balance:
        print("Not enough in bank.")
        return
    bank_balance -= amt
    balance += amt
    print(f"Withdrew ${amt:.2f}")

def buy_interest_upgrade():
    global balance, bank_interest_rate, bank_interest_cost
    if balance < bank_interest_cost:
        print("Not enough cash to buy interest upgrade.")
        return
    balance -= bank_interest_cost
    bank_interest_rate += 0.0025
    bank_interest_cost *= 1.25
    # apply easy mode bonus
    if mode == "Easy":
        bank_interest_rate += 0.0025
    print(f"Upgraded bank interest to {bank_interest_rate*100:.3f}% (Next cost: ${bank_interest_cost:.2f})")
    
    
# --- Certified Deposit (CD) System ---
active_cds = []
cd_history = []
cd_cooldown_until = 0               # when player can next open CDs
cds_opened_since_cooldown = 0       # tracks how many CDs opened since last cooldown

def bank_cd_menu():
    global active_cds, cd_history, cd_cooldown_until, cds_opened_since_cooldown
    global balance, bank_balance, days_passed

    while True:
        print("\n=== 💰 Certified Deposits (CD) Menu ===")
        print(f"📅 Current Day: {days_passed}")
        print(f"💵 Cash: {format_money(balance)} | 🏛️ Bank: {format_money(bank_balance)}")
        print(f"📜 Active CDs: {len(active_cds)}/5 | CDs opened since cooldown: {cds_opened_since_cooldown}/5")

        # --- Cooldown display ---
        if days_passed < cd_cooldown_until:
            print(f"🕒 Cooldown active! You can open new CDs in {cd_cooldown_until - days_passed} days.")
        print("----------------------------------------")

        # --- Display active CDs ---
        if active_cds:
            for i, cd in enumerate(active_cds, 1):
                days_left = cd["expire_day"] - days_passed
                status = "⏳ Locked"
                if days_left < 0 and not cd["claimed"]:
                    days_to_claim = cd["claim_deadline"] - days_passed
                    if days_to_claim >= 0:
                        status = f"✅ Ready to Claim ({days_to_claim}d left)"
                    else:
                        status = "❌ Forfeited"
                elif cd["claimed"]:
                    status = "🏁 Claimed"
                print(f"{i}) ${cd['amount']:,.2f} @ {cd['rate']*100:.2f}%/wk | "
                      f"{cd['lock_days']}d lock | {status} | Days Left: {max(days_left,0)}")
        else:
            print("No active CDs.")

        print("----------------------------------------")
        print("B) Open New CD")
        print("C) Claim Matured CDs")
        print("H) View CD History")
        print("Q) Exit CD Menu")
        choice = input("Choose: ").strip()

        # --- Open new CD ---
        if choice == "b":
            # Check cooldown
            if days_passed < cd_cooldown_until:
                print(f"🕒 You must wait {cd_cooldown_until - days_passed} more days before opening a new CD.")
                continue
            if len(active_cds) >= 5:
                print("❌ You already have 5 active CDs.")
                continue
            if cds_opened_since_cooldown >= 5:
                print("🕒 You've opened 5 CDs since your last cooldown. Please wait for your cooldown to reset.")
                cd_cooldown_until = days_passed + 90
                cds_opened_since_cooldown = 0
                continue

            # Generate random CD offers
            cd_options = []
            for _ in range(5):
                rate = random.uniform(0.002, 0.009)
                limit = random.randint(10000, 100000)
                lock = random.randint(90, 120)
                cd_options.append((rate, limit, lock))

            print("\nAvailable CD Offers:")
            for i, (r, l, d) in enumerate(cd_options, 1):
                print(f"{i}) {r*100:.2f}% weekly | Max ${l:,.0f} | {d} days locked")

            choice = input("Select offer (1-5) or cancel: ").strip()
            if not choice.isdigit() or not (1 <= int(choice) <= 5):
                continue
            idx = int(choice) - 1
            rate, limit, lock = cd_options[idx]

            try:
                amt = float(input(f"Enter deposit amount (max ${limit:,.2f}): "))
            except ValueError:
                print("Invalid amount.")
                continue
            if amt <= 0 or amt > limit:
                print("❌ Invalid amount.")
                continue
            if amt > bank_balance:
                print("❌ Not enough funds in bank.")
                continue

            # Deduct and store CD
            bank_balance -= amt
            cd = {
                "amount": amt,
                "rate": rate,
                "lock_days": lock,
                "start_day": days_passed,
                "expire_day": days_passed + lock,
                "claim_deadline": days_passed + lock + 30,
                "claimed": False
            }
            active_cds.append(cd)
            cds_opened_since_cooldown += 1
            print(f"✅ CD opened: {format_money(amt)} at {rate*100:.2f}% weekly for {lock} days.")

            # Trigger cooldown automatically when total reaches 5
            if cds_opened_since_cooldown >= 5:
                cd_cooldown_until = days_passed + 200
                cds_opened_since_cooldown = 0
                print(f"🕒 Cooldown started for 200 days! You cannot open new CDs until day {cd_cooldown_until}.")

        # --- Claim matured CDs ---
        elif choice == "c":
            claimed_any = False
            failed_any = False
            for cd in list(active_cds):
                if cd["claimed"]:
                    continue

                # Forfeited CDs
                if days_passed > cd["claim_deadline"]:
                    print(f"❌ CD of {format_money(cd['amount'])} expired and unclaimed. Lost.")
                    cd_history.append({
                        "amount": cd["amount"],
                        "rate": cd["rate"],
                        "start_day": cd["start_day"],
                        "expire_day": cd["expire_day"],
                        "result": "❌ Forfeited"
                    })
                    active_cds.remove(cd)
                    failed_any = True
                    continue

                # Matured CDs
                if days_passed >= cd["expire_day"]:
                    weeks = cd["lock_days"] // 7
                    total_interest = cd["amount"] * cd["rate"] * weeks
                    payout = cd["amount"] + total_interest
                    bank_balance += payout
                    cd["claimed"] = True
                    cd_history.append({
                        "amount": cd["amount"],
                        "rate": cd["rate"],
                        "start_day": cd["start_day"],
                        "expire_day": cd["expire_day"],
                        "result": "✅ Claimed",
                        "interest": total_interest
                    })
                    active_cds.remove(cd)
                    print(f"✅ Claimed CD worth {format_money(payout)} (includes {format_money(total_interest)} interest).")
                    claimed_any = True

            if not claimed_any and not failed_any:
                print("No CDs ready for claiming or forfeited.")

        # --- View CD History ---
        elif choice == "h":
            print("\n=== 🗂️ CD History ===")
            if not cd_history:
                print("No CD records yet.")
            else:
                for h in cd_history[-10:]:
                    result = h.get("result", "Unknown")
                    rate = h["rate"] * 100
                    print(f"💾 {result}: ${h['amount']:,.2f} @ {rate:.2f}% "
                          f"| Started Day {h['start_day']} | Expired Day {h['expire_day']}")
                    if "interest" in h:
                        print(f"   💵 Earned: {format_money(h['interest'])}")
            print("========================")

        elif choice == "q":
            break
        else:
            print("Invalid option.")


def process_cds():
    """Apply weekly interest to active CDs."""
    global active_cds, days_passed
    for cd in active_cds:
        if cd["claimed"]:
            continue
        if days_passed > cd["expire_day"]:
            continue
        if (days_passed - cd["start_day"]) % 7 == 0 and days_passed != cd["start_day"]:
            weekly_interest = cd["amount"] * cd["rate"]
            cd["amount"] += weekly_interest
            print(f"💰 CD earned {format_money(weekly_interest)} in interest (total {format_money(cd['amount'])}).")



# --- Save/Load ---
def save_game():
    """Save all game data to JSON file (including Vegas jackpot, stats, and CDs)."""
    global balance, bank_balance, days_passed, portfolio, stocks, trade_history
    global insider_predictions, black_market_orders, heist_inventory, heist_wanted_flags
    global heist_history, player_has_fake_id, insider_info_cost, price_history, black_market_history
    global FAKE_ID_COST, fake_id_locked_until, last_fast_forward_day
    global bank_interest_rate, next_interest_day, bank_interest_cost
    global vegas_jackpot, vegas_stats  # ✅ ensure vegas_stats included
    global active_cds, cd_history, cd_cooldown_until, cds_opened_since_cooldown, cryptos, crypto_portfolio, crypto_supply, crypto_history   # ✅ include Certified Deposits

    if "vegas_jackpot" not in globals():
        vegas_jackpot = 25000.0  # ensure default if missing
    if "vegas_stats" not in globals() or not isinstance(vegas_stats, dict):
        vegas_stats = {
            "slots_played": 0,
            "blackjack_wins": 0,
            "blackjack_losses": 0,
            "roulette_bets": 0,
            "jackpots_won": 0,
            "games_played": 0,
            "total_bets": 0.0,
            "total_won": 0.0,
            "total_lost": 0.0,
            "net": 0.0
        }

    data = {
        "balance": balance,
        "bank_balance": bank_balance,
        "days_passed": days_passed,
        "portfolio": portfolio,
        "stocks": stocks,
        "insider_predictions": insider_predictions,
        "black_market_orders": black_market_orders,
        "heist_inventory": heist_inventory,
        "heist_wanted_flags": heist_wanted_flags,
        "heist_history": heist_history,
        "player_has_fake_id": player_has_fake_id,
        "insider_info_cost": insider_info_cost if "insider_info_cost" in globals() else 10000,
        "price_history": price_history,
        "black_market_history": black_market_history,
        "FAKE_ID_COST": FAKE_ID_COST,
        "fake_id_locked_until": fake_id_locked_until,
        "last_fast_forward_day": last_fast_forward_day,
        "bank_interest_rate": bank_interest_rate,
        "bank_interest_cost": bank_interest_cost,
        "next_interest_day": next_interest_day,
        "vegas_jackpot": vegas_jackpot,  # ✅ Jackpot saved here
        "vegas_stats": vegas_stats,      # ✅ Stats saved too
        "active_cds": active_cds,        # ✅ Save active CDs
        "cd_history": cd_history,        # ✅ Save CD history
        "cd_cooldown_until": cd_cooldown_until,
        "cds_opened_since_cooldown": cds_opened_since_cooldown,
        "trade_history": trade_history,
        "cryptos": cryptos,
        "crypto_portfolio": crypto_portfolio,
        "crypto_supply": crypto_supply,
        "crypto_history": crypto_history,
        
    }

    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=4)
        print("💾 Game saved successfully.")
    except Exception as e:
        print(f"⚠️ Error saving game: {e}")


def load_game():
    """Load all game data from JSON file (including Vegas jackpot, stats, and CDs)."""
    global balance, bank_balance, days_passed, portfolio, stocks, trade_history
    global insider_predictions, black_market_orders, heist_inventory, heist_wanted_flags
    global heist_history, player_has_fake_id, insider_info_cost, price_history, black_market_history
    global FAKE_ID_COST, fake_id_locked_until, last_fast_forward_day
    global bank_interest_rate, next_interest_day, bank_interest_cost
    global vegas_jackpot, vegas_stats  # ✅ ensure vegas_stats is properly global
    global active_cds, cd_history, cd_cooldown_until, cds_opened_since_cooldown, cryptos, crypto_portfolio, crypto_supply, crypto_history  # ✅ include Certified Deposits

    if not os.path.exists(SAVE_FILE):
        print("📄 No save file found. Starting a new game.")
        balance = 5000.0
        bank_balance = 0.0
        bank_interest_rate = 0.0
        bank_interest_cost = 10000.0
        next_interest_day = 7
        portfolio, stocks, insider_predictions = {}, {}, {}
        black_market_orders, heist_inventory, heist_wanted_flags = [], {}, []
        heist_history, price_history, black_market_history = [], {}, []
        player_has_fake_id = False
        FAKE_ID_COST = 15000.0
        fake_id_locked_until = 0
        last_fast_forward_day = None
        vegas_jackpot = 25000.0
        vegas_stats = {  # ✅ initialize vegas_stats for new game
            "slots_played": 0,
            "blackjack_wins": 0,
            "blackjack_losses": 0,
            "roulette_bets": 0,
            "jackpots_won": 0,
            "games_played": 0,
            "total_bets": 0.0,
            "total_won": 0.0,
            "total_lost": 0.0,
            "net": 0.0
        }
        active_cds, cd_history = [], []  # ✅ initialize new CD lists
        return

    try:
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading save file: {e}")
        return

    # Restore core stats
    balance = data.get("balance", 5000.0)
    bank_balance = data.get("bank_balance", 0.0)
    days_passed = data.get("days_passed", 0)
    portfolio = data.get("portfolio", {})
    stocks = data.get("stocks", {})
    insider_predictions = data.get("insider_predictions", {})
    black_market_orders = data.get("black_market_orders", [])
    heist_inventory = data.get("heist_inventory", {})
    heist_wanted_flags = data.get("heist_wanted_flags", [])
    heist_history = data.get("heist_history", [])
    player_has_fake_id = data.get("player_has_fake_id", False)
    insider_info_cost = data.get("insider_info_cost", 10000)
    price_history = data.get("price_history", {})
    black_market_history = data.get("black_market_history", [])
    FAKE_ID_COST = data.get("FAKE_ID_COST", 15000.0)
    fake_id_locked_until = data.get("fake_id_locked_until", 0)
    last_fast_forward_day = data.get("last_fast_forward_day", None)
    bank_interest_rate = data.get("bank_interest_rate", 0.0)
    bank_interest_cost = data.get("bank_interest_cost", 10000.0)
    next_interest_day = data.get("next_interest_day", 7)
    vegas_jackpot = data.get("vegas_jackpot", 25000.0)
    cd_cooldown_until = data.get("cd_cooldown_until", 0)
    cds_opened_since_cooldown = data.get("cds_opened_since_cooldown", 0)
    trade_history = data.get("trade_history", [])
    cryptos = data.get("cryptos", {})
    crypto_portfolio = data.get("crypto_portfolio", {})
    crypto_supply = data.get("crypto_supply", {})
    crypto_history = data.get("crypto_history", {})



    # ✅ Load Certified Deposit data
    active_cds = data.get("active_cds", [])
    cd_history = data.get("cd_history", [])

    # ✅ Cleanup corrupted or legacy CD entries
    active_cds = [cd for cd in active_cds if isinstance(cd, dict) and "amount" in cd]
    cd_history = [h for h in cd_history if isinstance(h, dict) and "amount" in h]

    # ✅ Restore Vegas stats properly with fallback
    vegas_stats = data.get("vegas_stats", {
        "slots_played": 0,
        "blackjack_wins": 0,
        "blackjack_losses": 0,
        "roulette_bets": 0,
        "jackpots_won": 0,
        "games_played": 0,
        "total_bets": 0.0,
        "total_won": 0.0,
        "total_lost": 0.0,
        "net": 0.0
    })

    # Ensure all numeric values exist even if older saves are missing them
    for k, v in {
        "games_played": 0,
        "total_bets": 0.0,
        "total_won": 0.0,
        "total_lost": 0.0,
        "net": 0.0
    }.items():
        vegas_stats[k] = vegas_stats.get(k, v)

    print("✅ Game loaded successfully.")



# --- Fast Forward & Auto ---
def fast_forward(days=None):
    """
    Fast-forward the game by `days` in-game days.
    Adds a 7-day cooldown after use so it can't be reused until 7 in-game days later.
    """
    global days_passed, bank_balance, stocks, price_history, insider_predictions
    global black_market_orders, black_market_history, balance, heist_wanted_flags
    global last_fast_forward_day, bank_interest_rate, vegas_jackpot, process_cds, update_cryptos

    # --- Check cooldown ---
    if last_fast_forward_day is not None:
        days_since_last = days_passed - last_fast_forward_day
        remaining = FAST_FORWARD_COOLDOWN_DAYS - days_since_last
        if remaining > 0:
            print(f"\n⚠️ Fast Forward is on cooldown. You must wait {remaining} more in-game day(s).")
            return

    # Prompt if not provided
    if days is None:
        try:
            days = int(input("⏩ How many days do you want to fast forward? ").strip())
        except Exception:
            print("Invalid input. Fast-forward cancelled.")
            return

    if days <= 0:
        print("You must enter a positive number of days.")
        return

    # Charge $100/day from bank (allow partial if not enough)
    cost_per_day = 500
    total_cost = days * cost_per_day
    if bank_balance < total_cost:
        affordable_days = int(bank_balance // cost_per_day)
        if affordable_days == 0:
            print(f"Not enough funds in bank to fast-forward even 1 day (need ${cost_per_day:,} per day).")
            return
        print(f"⚠️ Bank has ${bank_balance:,.2f}. Can only afford {affordable_days} day(s). Fast-forwarding {affordable_days} day(s) instead.")
        days_to_run = affordable_days
    else:
        days_to_run = days

    # Deduct cost
    ded_cost = days_to_run * cost_per_day
    bank_balance -= ded_cost

    print(f"\n⏩ Fast forwarding {days_to_run} day(s) (charged ${ded_cost:,.2f} from bank)...")
    time.sleep(0.6)

    for _ in range(days_to_run):
        # --- Advance day counter ---
        days_passed += 1
        process_cds()
        update_cryptos()
        # --- Update all stock prices ---
        for name in list(stocks.keys()):
            S = stocks[name]
            Z = np.random.normal()

            # Insider info influence (if active)
            if name in insider_predictions and insider_predictions[name].get("days_left", 0) > 0:
                info = insider_predictions[name]
                direction = info.get("trend", "up")
                accuracy = info.get("accuracy", False)
                bias = 0.02 if (direction == "up" and accuracy) or (direction == "down" and not accuracy) else -0.02
                Z += bias
                insider_predictions[name]["days_left"] -= 1
                if insider_predictions[name]["days_left"] <= 0:
                    del insider_predictions[name]
                    print(f"🕒 Insider info for {name} has expired.")

            # Update price (Geometric Brownian Motion)
            S_new = S * np.exp((DAILY_DRIFT - 0.5 * DAILY_VOLATILITY**2) + DAILY_VOLATILITY * Z)
            stocks[name] = round(max(0.01, S_new), 2)
            price_history.setdefault(name, []).append(stocks[name])

        # --- Daily updates ---
        if 'apply_bank_interest' in globals() and days_passed >= next_interest_day:
            apply_bank_interest()
        if 'process_black_market_orders' in globals():
            process_black_market_orders()
        if 'process_heist_wanted' in globals():
            process_heist_wanted()
        if 'auto_save_if_needed' in globals():
            auto_save_if_needed()
        # Daily jackpot growth
        if "vegas_jackpot" in globals():
            vegas_jackpot += 500.0


    # --- Mark cooldown start ---
    last_fast_forward_day = days_passed
    save_game()

    print(f"✅ Fast forward complete. Now at day {days_passed}.")
    print(f"⏳ You must wait {FAST_FORWARD_COOLDOWN_DAYS} in-game days before using Fast Forward again.")


def auto_save_if_needed():
    """Auto-save the game every AUTO_SAVE_INTERVAL days."""
    global last_auto_save_day
    if days_passed - last_auto_save_day >= AUTO_SAVE_INTERVAL:
        save_game()
        last_auto_save_day = days_passed

def apply_bank_interest():
    """Apply weekly interest to the player's bank balance (every 7 in-game days)."""
    global bank_balance, bank_interest_rate, next_interest_day, days_passed

    # Check if it’s time to apply interest
    if days_passed >= next_interest_day:
        if bank_balance > 0 and bank_interest_rate > 0:
            interest = bank_balance * bank_interest_rate
            bank_balance += interest
            print(f"🏦 Weekly interest of {format_money(interest)} added to your bank balance!")

        # Schedule next interest payout
        next_interest_day = days_passed + 7
        save_game()

        # --- Start cooldown ---
        last_fast_forward_day = day
        print_stocks(current_page)
        print_portfolio()

def auto_play():
    """Background auto-update loop (run in a thread)."""
    global play_mode, days_passed, bank_balance, bank_interest_rate, current_page, vegas_jackpot, update_cryptos, process_cds

    tick_count = 0  # counts 15-second updates

    while play_mode:
        tick_count += 1
        
    # Daily jackpot growth
        if "vegas_jackpot" in globals():
            vegas_jackpot += 125.0


        # --- Update all stock prices ---
        for name in list(stocks.keys()):
            S = stocks[name]
            Z = np.random.normal()

            # --- Insider info influence ---
            if name in insider_predictions and insider_predictions[name]["days_left"] > 0:
                info = insider_predictions[name]
                direction = info.get("trend", info.get("predicted_direction", "neutral"))
                accuracy = info.get("accuracy", 0.65)
                bias = 0.02 if (direction == "up" and accuracy) or (direction == "down" and not accuracy) else -0.02
                Z += bias  # small bias in expected direction
                insider_predictions[name]["days_left"] -= 1
                if insider_predictions[name]["days_left"] <= 0:
                    print(f"🕒 Insider info for {name} has expired.")

            S_new = S * np.exp((DAILY_DRIFT - 0.5 * DAILY_VOLATILITY**2) + DAILY_VOLATILITY * Z)
            stocks[name] = round(max(0.01, S_new), 2)
            price_history.setdefault(name, []).append(stocks[name])

        # --- Every 4 updates = 1 in-game day ---
        if tick_count % 4 == 0:
            days_passed += 1
            auto_save_if_needed()
            apply_bank_interest()
            process_black_market_orders()
            process_heist_wanted()
            process_cds()
            update_cryptos()

        # --- Clear terminal and display market ---
        os.system("cls" if os.name == "nt" else "clear")
        print(f"📅 Day: {days_passed} | ⏱️ Market Tick #{tick_count}")
        print_stocks(current_page)
        print_portfolio()

        # --- Wait 15 seconds before next update ---
        time.sleep(15)

def process_heist_wanted():
    """Called each new in-game day: decrement wanted flags and roll for capture."""
    global heist_wanted_flags, bank_balance, balance, heist_history, player_has_fake_id, FAKE_ID_COST
    if not heist_wanted_flags:
        return
    for flag in list(heist_wanted_flags):
        # Each day sample the daily catch probability
        if random.random() < flag.get("daily_catch_p", 0):
            # caught!
            print(f"\n🚨 You have been caught for a {flag['type']} heist! Authorities seize your bank account.")
            # Lose all money in bank account
            bank_balance = 0.0
            # Optionally also confiscate fake ID
            if player_has_fake_id:
                player_has_fake_id = False
                FAKE_ID_COST = round(FAKE_ID_COST * FAKE_ID_COST_INCREASE, 2)
                print(f"⚠️ Your Fake ID was confiscated. New Fake ID cost is {format_money(FAKE_ID_COST)}.")
            heist_history.append({"type": flag["type"], "result": "Caught", "day": days_passed, "gain": 0})
            heist_wanted_flags.remove(flag)
            save_game()
            # If caught, we stop checking other flags this day to let the player react next loop
            return
        else:
            flag["days_left"] -= 1
            if flag["days_left"] <= 0:
                # period ended without capture
                heist_history.append({"type": flag["type"], "result": "Period expired - not caught", "day": days_passed, "gain": 0})
                heist_wanted_flags.remove(flag)
    # auto-save after processing
    save_game()


# --- Game Mode  ---
def choose_game_mode():
    """Prompt player for mode. Ensure stocks exist before using them."""
    global balance, bank_interest_rate, bank_interest_cost, portfolio, stocks, mode

    # Ensure market exists if somehow empty
    if not stocks:
        print("Generating market data...")
        # regenerate stocks and associated histories/supplies
        new_stocks = generate_stocks()
        stocks.clear()
        stocks.update(new_stocks)
        for s in list(stocks.keys()):
            stock_supply[s] = random.randint(10000, 1000000)
            price_history.setdefault(s, generate_stock_history(stocks[s], days=random.randint(30, 100)))

    print("\n=== 🎮 Choose Your Game Mode ===")
    print("1) 🟢 Easy Mode   - Start with $10k and 1 random stock (1–10 shares).")
    print("                  - Cheaper stock prices, cheaper interest upgrades.")
    print("2) ⚪ Normal Mode - The standard stock market experience.")
    print("3) 🔴 Hard Mode   - Start with only $1500 and tougher conditions.")
    print("\n=== 🎰 7 Casino Games in Vegas 🎰 ===")
    print("\n=== 🎮 Two Hidden Menus... One Gameplay Enhancement... And Two Hidden Gamemodes 🎮 ===")
    print("HINT: One option is for knowledge, the two gamemodes are HIGHLY ILLEGAL and can be found at the same place.")
    print()
    print("\nVer: 1.0.5")

    while True:
        choice = input("\nSelect mode (1=Easy, 2=Normal, 3=Hard): ").strip()
        if choice not in ["1", "2", "3"]:
            print("Invalid choice. Please enter 1, 2, or 3.")
            continue
        break

    # Default values
    balance = 5000.0
    bank_interest_rate = 0.0
    bank_interest_cost = 10000.0
    mode = "Normal"

    if choice == "1":  # Easy Mode
        mode = "Easy"
        bank_interest_cost *= 0.5
        balance = 10000.0
        print("\n🟢 Easy Mode Selected!")
        print("You start with one random stock and cheaper prices.")

        # Adjust all stock prices (50% cheaper)
        for s in list(stocks.keys()):
            stocks[s] = round(float(stocks[s]) * 0.5, 2)
            # ensure price_history exists (and update it to reflect adjusted price)
            if s not in price_history:
                price_history[s] = generate_stock_history(stocks[s], days=60)
            else:
                # append current price to history to reflect new starting price
                price_history[s].append(stocks[s])

        # Give one random stock (safe because stocks guaranteed non-empty)
        random_stock = random.choice(list(stocks.keys()))
        owned_qty = random.randint(1, 10)
        portfolio[random_stock] = {"qty": owned_qty, "avg_price": stocks[random_stock]}
        print(f"You start owning {owned_qty} shares of {random_stock} (${stocks[random_stock]:.2f} each).")

        print("Bank interest upgrades give double the boost in Easy mode (effect applied in upgrade logic).")

    elif choice == "2":  # Normal
        mode = "Normal"
        print("\n⚪ Normal Mode Selected! Classic balanced gameplay.")

    elif choice == "3":  # Hard
        mode = "Hard"
        balance = 1500.0
        bank_interest_cost *= 2
        print("\n🔴 Hard Mode Selected! Money is tight, interest upgrades cost more.")
        print("Bank upgrades cost double, and returns are reduced. Play carefully!")

    print(f"\n💰 Starting balance: ${balance:,.2f}")
    print(f"🏛️ Bank interest rate: {bank_interest_rate*100:.2f}%")
    print(f"💸 Interest upgrade cost: ${bank_interest_cost:,.2f}")
    print(f"🎯 Mode: {mode}\n")

def new_game():
    """Wipes save data and restarts from game mode selection."""
    global balance, bank_balance, bank_interest_rate, bank_interest_cost
    global portfolio, stocks, day, next_interest_day, mode, price_history, stock_supply
    global shorts, trade_history, purchased_dlcs, dlc_stocks_unlocked, days_passed
    global last_auto_save_day, vegas_stats, INSIDER_INFO_COST
    global last_fast_forward_day, FAST_FORWARD_COOLDOWN_DAYS, heist_wanted_flags, heist_inventory, heist_history


    confirm = input("⚠️ Are you sure you want to start a NEW GAME? This will erase all progress! (yes/no): ").strip().lower()
    if confirm != "yes":
        print("❌ New game canceled.")
        return

    # Delete save file
    if os.path.exists(SAVE_FILE):
        try:
            os.remove(SAVE_FILE)
            print("🗑️ Existing save data deleted!")
        except Exception as e:
            print(f"Error deleting save file: {e}")

    # Reset all variables
    balance = 5000.0
    bank_balance = 0.0
    bank_interest_rate = 0.0
    bank_interest_cost = 10000.0
    portfolio = {}
    shorts = {}
    trade_history = []
    price_history = {}
    stock_supply = {}
    purchased_dlcs.clear()
    dlc_stocks_unlocked.clear()
    days_passed = 0
    last_auto_save_day = 0
    day = 1
    next_interest_day = 7
    mode = "Normal"
    INSIDER_INFO_COST = 10000 
    black_market_inventory.clear()
    black_market_orders.clear()
    insider_predictions.clear()
    black_market_history.clear()
    player_has_fake_id = False
    FAKE_ID_COST = 15000
    heist_inventory = {}
    heist_wanted_flags = []
    heist_history = []
    insider_info_cost = 10000
    last_fast_forward_day = None
    fake_id_locked_until = 0
    bank_interest_rate = 0.00  # example: 2% per week
    next_interest_day = 7      # first interest after day 7
    vegas_jackpot = 25000.0
    NEW_GAME_FLAG = True
    NEW_GAME_FLAG = True
    load_game()
    NEW_GAME_FLAG = False
    # --- Reset Certified Deposit System ---
    active_cds = []
    cd_history = []
    cd_cooldown_until = 0
    cds_opened_since_cooldown = 0
    cryptos.clear()
    crypto_portfolio.clear()
    crypto_supply.clear()
    crypto_history.clear()





    vegas_stats = {
        "total_bets": 0.0,
        "games_played": 0,
        "total_won": 0.0,
        "total_lost": 0.0,
        "net": 0.0
    }

    # Regenerate base stocks and their histories/supply
    new_stocks = generate_stocks()
    stocks.clear()
    stocks.update(new_stocks)
    for s in list(stocks.keys()):
        stock_supply[s] = random.randint(10000, 1000000)
        price_history[s] = generate_stock_history(stocks[s], days=random.randint(30, 100))

    # Let player choose mode (now stocks exist so easy mode safe)
    choose_game_mode()

    # Save initial game
    save_game()
    print("✅ New game started successfully!\n")

# -------------------------
# --- VEGAS / CASINO CODE (Animated Slots, Wheel, Roulette, Blackjack)
# -------------------------

def format_money(x): return f"${x:,.2f}"

# --- Vegas Hub Settings ---
VEGAS_TABLE_MIN = 75  # universal minimum bet for all Vegas games

# ---------- Vegas Hub ----------
def vegas_menu():
    """Main Vegas hub: shows stats and options for mini-games."""
    global vegas_stats
    while True:
        print(f"\n🎲 Welcome to the Vegas Hub — Table Minimum: ${VEGAS_TABLE_MIN:,}\n")
        print(f"Cash: {format_money(balance)} | Bank: {format_money(bank_balance)}")
        print("\nVegas Stats:")
        print(f" - Games Played: {vegas_stats.get('games_played', 0)}")
        print(f" - Total Bets: {format_money(vegas_stats.get('total_bets',0.0))}")
        print(f" - Total Won: {format_money(vegas_stats.get('total_won',0.0))}")
        print(f" - Total Lost: {format_money(vegas_stats.get('total_lost',0.0))}")
        print(f" - Net: {format_money(vegas_stats.get('net',0.0))}")
        print("\nChoose a game:")
        print("1) 🎰 Slots")
        print("2) 🎡 Roulette")
        print("3) ♠🃏 21 (Blackjack)")
        print("4) 🐎 Horse Races")
        print("5) 🧱 Stack 'Em")
        print("6) 🎲 Craps")
        print("7) 🟡 Plinko Drop")
        print("Q) Leave Vegas")
        choice = input("Select (1-7 & Q ): ").strip()
        if choice == "1":
            vegas_slots()
        elif choice == "4":
            vegas_horse_race()
        elif choice == "2":
            vegas_roulette()
        elif choice == "3":
            vegas_blackjack()
        elif choice == "5":
            vegas_stack_em()
        elif choice == "6":
            vegas_craps()
        elif choice == "7":
            vegas_plinko()
        elif choice == "q":
            print("Leaving Vegas...")
            break
        else:
            print("Invalid choice. Enter 1-7 & Q.")

def vegas_place_bet():
    """Ask player to place a bet with universal table minimum."""
    global balance
    while True:
        try:
            print(f"\n🎰 Table Minimum Bet: ${VEGAS_TABLE_MIN:,}")
            bet_input = input("Enter your bet amount or press Enter to cancel: ").strip()
            if bet_input == "":
                print("Bet canceled.")
                return None
            bet = float(bet_input)
            if bet < VEGAS_TABLE_MIN:
                print(f"❌ The table minimum is ${VEGAS_TABLE_MIN:,}. Please increase your bet.")
                continue
            if bet > balance:
                print("❌ You don't have enough money for that bet.")
                continue
            return bet
        except ValueError:
            print("❌ Invalid bet amount.")

def vegas_record_result(bet, net):
    global vegas_stats

    # Make sure vegas_stats exists and is a dict
    if not isinstance(vegas_stats, dict):
        vegas_stats = {
            "games_played": 0,
            "total_bets": 0.0,
            "total_won": 0.0,
            "total_lost": 0.0,
            "net": 0.0
        }

    s = vegas_stats
    s["games_played"] = s.get("games_played", 0) + 1
    s["total_bets"] = s.get("total_bets", 0.0) + bet
    if net > 0:
        s["total_won"] = s.get("total_won", 0.0) + net
    elif net < 0:
        s["total_lost"] = s.get("total_lost", 0.0) + abs(net)

    s["net"] = s.get("total_won", 0.0) - s.get("total_lost", 0.0)

    # Always save after updating stats
    try:
        save_game()
        print("💾 Vegas progress auto-saved.")
    except Exception as e:
        print(f"⚠️ Save failed: {e}")


# -------------------------
# Slots with realistic animation
# -------------------------
def vegas_slots():
    """🎰 3x3 Vegas Slot Machine with 5 win lines, progressive jackpot 💎, and spinning animation."""
    global balance, vegas_jackpot

    # Initialize jackpot if missing
    if "vegas_jackpot" not in globals():
        vegas_jackpot = 25000.0

    print("\n--- 🎰 Vegas Slots ---")
    print(f"💰 Current Jackpot: {format_money(vegas_jackpot)}")

    bet = vegas_place_bet()
    if not bet:
        return

    balance -= bet

    # Jackpot only increases from bets (not daily)
    vegas_jackpot += bet * 0.05

    symbols = ["🍒", "🍋", "🔔", "🍀", "💎", "7️⃣", "🍇"]
    reels = [[random.choice(symbols) for _ in range(3)] for _ in range(3)]

    spin_frames = 20
    delay = 0.15

    print("\nSpinning...\n")
    time.sleep(0.5)

    final_grid = [[None for _ in range(3)] for _ in range(3)]
    for reel in range(3):
        for frame in range(spin_frames):
            os.system("cls" if os.name == "nt" else "clear")
            print("🎰 --- VEGAS SLOTS --- 🎰")
            print(f"💰 Jackpot: {format_money(vegas_jackpot)}")
            print("--------------------------")

            temp_grid = []
            for r in range(3):
                row = []
                for c in range(3):
                    if c <= reel:
                        row.append(final_grid[r][c] if final_grid[r][c] else random.choice(symbols))
                    else:
                        row.append(random.choice(symbols))
                temp_grid.append(row)

            for row in temp_grid:
                print(" | ".join(row))
            print("--------------------------")
            time.sleep(delay)

        # Lock in final symbols for this reel
        for r in range(3):
            final_grid[r][reel] = random.choice(symbols)

    # Final reveal
    os.system("cls" if os.name == "nt" else "clear")
    print("\n🎰 --- VEGAS SLOTS --- 🎰")
    print(f"💰 Jackpot: {format_money(vegas_jackpot)}")
    print("--------------------------")
    for row in final_grid:
        print(" | ".join(row))
    print("--------------------------")

    # Win lines: 3 horizontal, 2 diagonal
    win_lines = [
        [(0, 0), (0, 1), (0, 2)],
        [(1, 0), (1, 1), (1, 2)],
        [(2, 0), (2, 1), (2, 2)],
        [(0, 0), (1, 1), (2, 2)],
        [(0, 2), (1, 1), (2, 0)],
    ]

    total_winnings = 0.0
    jackpot_hit = False

    for line in win_lines:
        line_syms = [final_grid[r][c] for r, c in line]
        if line_syms.count(line_syms[0]) == 3:
            sym = line_syms[0]
            if sym == "💎":
                winnings = vegas_jackpot
                jackpot_hit = True
                vegas_jackpot = 25000.0
                print(colored(f"\n💎 JACKPOT! 3 💎 in a row — you win {format_money(winnings)}!", "93"))
            else:
                payouts = {
                    "🍒": 4.0,
                    "🍋": 3.0,
                    "🔔": 6.0,
                    "🍀": 8.0,
                    "7️⃣": 12.0,
                    "🍇": 5.0,
                }
                multiplier = payouts.get(sym, 2.0)
                winnings = bet * multiplier
                print(f"🎉 {sym*3} — You won {format_money(winnings)}!")
            total_winnings += winnings

    if total_winnings > 0:
        balance += total_winnings
        vegas_record_result(bet, total_winnings)
    else:
        print("😢 No winning lines this time. Try again!")
        vegas_record_result(bet, -bet)

    print(f"\n💰 Your balance: {format_money(balance)}")
    print_portfolio()
    save_game()
    time.sleep(2)


# ---------- Horse Race ----------
def vegas_horse_race():
    """Animated horse race betting game 🏇 with aligned finish line and bet highlight."""
    global balance
    print("\n--- 🏇 Horse Race ---")
    print("There are 10 horses in the race!")

    try:
        pick = int(input("Pick your horse (1-10): "))
    except ValueError:
        print("Invalid selection.")
        return

    if pick < 1 or pick > 10:
        print("Choose between 1 and 10.")
        return

    bet = vegas_place_bet()
    if not bet:
        return

    horses = ["🏇"] * 10
    track_length = 65  # Total distance to finish line
    positions = [0] * 10
    winner = None

    print("\nThe race is about to begin!")
    for count in ["3", "2", "1", "GO!"]:
        print(count)
        time.sleep(0.6)

    time.sleep(0.6)

    while not winner:
        os.system("cls" if os.name == "nt" else "clear")
        print("🐎 Horse Race Track\n")

        for i, horse in enumerate(horses):
            pos = positions[i]

            # Player's chosen horse highlighted green
            if i + 1 == pick:
                horse_icon = "🟢🏇"
            else:
                horse_icon = "🏇"

            # Calculate consistent spacing
            line = " " * pos + horse_icon
            spaces_to_finish = max(0, track_length - pos)

            # Normalize spacing: trim or pad to make all finish lines align
            if len(horse_icon) > 1:
                spaces_to_finish = max(0, track_length - pos - 1)

            # Draw horse and finish line perfectly aligned
            print(f"{line}{' ' * spaces_to_finish}🏁 ({i+1})")

        # Move horses randomly forward
        for i in range(len(horses)):
            positions[i] += random.randint(0, 2)
            if positions[i] >= track_length:
                positions[i] = track_length
                if not winner:
                    winner = i + 1

        time.sleep(0.1)

    print(f"\n🏁 Horse #{winner} wins the race!")

    # Payout logic
    if pick == winner:
        winnings = bet * 9.5
        balance += winnings
        print(f"🎉 You won {format_money(winnings)}! ({9.5}x payout)")
        vegas_record_result(bet, winnings)
    else:
        balance -= bet
        print(f"😢 You lost {format_money(bet)}. Better luck next time!")
        vegas_record_result(bet, -bet)

    print_portfolio()
    time.sleep(2)


# ---------- Roulette (fast, colored emoji animation) ----------
def vegas_roulette():
    """Roulette: bet color or exact number. Adds colored emojis for realism."""
    global balance
    print("\n--- 🎯 Roulette ---")
    print("1) Color (R/B)")
    print("2) Exact number (0-36)")
    choice = input("Choose bet type (1/2): ").strip()
    if choice not in ("1", "2"):
        return
    bet = vegas_place_bet()
    if not bet:
        return

    # --- color or number bet setup ---
    if choice == "1":
        color_choice = input("Choose color (R/B): ").strip().lower()
        if color_choice not in ("r", "b"):
            print("Invalid color.")
            return
    else:
        try:
            number_choice = int(input("Enter number (0-36): "))
        except ValueError:
            print("Invalid number.")
            return
        if number_choice < 0 or number_choice > 36:
            print("Out of range.")
            return

    # --- animation of the spin ---
    print("Spinning roulette wheel...")
    delay = 0.015  # faster starting speed
    for i in range(55):  # fewer steps = faster spin
        n = random.randint(0, 36)
        if n == 0:
            color = "g"; emoji = "🟢"; col_text = f"\033[92m{emoji} {n:2d}\033[0m"
        elif n % 2 == 0:
            color = "r"; emoji = "🔴"; col_text = f"\033[91m{emoji} {n:2d}\033[0m"
        else:
            color = "b"; emoji = "⚫"; col_text = f"\033[97m{emoji} {n:2d}\033[0m"
        sys.stdout.write(f"\rBall -> {col_text}   ")
        sys.stdout.flush()
        time.sleep(delay)
        delay *= 1.05  # smaller slowdown factor
    print()

    # --- final result ---
    landed = random.randint(0, 36)
    if landed == 0:
        color = "g"; emoji = "🟢"; cname = "\033[92mGreen\033[0m"
    elif landed % 2 == 0:
        color = "r"; emoji = "🔴"; cname = "\033[91mRed\033[0m"
    else:
        color = "b"; emoji = "⚫"; cname = "\033[97mBlack\033[0m"

    print(f"Ball lands on {emoji} {landed} ({cname})")

    # --- evaluate result ---
    win = 0
    if choice == "1":
        if color_choice == color:
            win = bet * 1.9
            balance += win
            print(f"You win {format_money(win)}! 🎉")
        else:
            balance -= bet
            win = -bet
            print(f"You lost {format_money(bet)}.")
    else:
        if number_choice == landed:
            win = bet * 30
            balance += win
            print(f"Exact hit! You won {format_money(win)}! 🥳")
        else:
            balance -= bet
            win = -bet
            print(f"Missed {format_money(bet)}.")
    
    vegas_record_result(bet, win)
    print_portfolio()


# ---------- Blackjack ----------
def vegas_blackjack():
    """Blackjack mini-game with emoji cards, colored suits, and end-of-round summary."""
    global balance
    print("\n--- 🃏 Vegas Blackjack ---")
    bet = vegas_place_bet()
    if not bet:
        return

    # --- Suit and color setup ---
    suits = ['♠️', '♥️', '♦️', '♣️']
    red_suits = ['♥️', '♦️']
    values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"

    # --- Blackjack session tracker ---
    session_profit = 0

    def colored_card(value, suit):
        """Return colored, emoji-enhanced card string."""
        if suit in red_suits:
            color_code = "\033[91m"  # red
        else:
            color_code = "\033[97m"  # white
        reset = "\033[0m"
        return f"{color_code}[{value}{suit}]{reset}"

    def draw_card():
        """Draw random card."""
        return random.choice(values), random.choice(suits)

    def calculate_total(hand):
        """Calculate hand value (Aces flexible)."""
        total, aces = 0, 0
        for value, suit in hand:
            if value in ['J', 'Q', 'K']:
                total += 10
            elif value == 'A':
                total += 11
                aces += 1
            else:
                total += int(value)
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    def display_hands(player_hand, dealer_hand, hide_dealer=False):
        """Show current game state with emoji and color formatting."""
        print("\n" + "═" * 50)
        if hide_dealer:
            dealer_display = [colored_card('?', '🎴'), colored_card(*dealer_hand[1])]
        else:
            dealer_display = [colored_card(v, s) for v, s in dealer_hand]
        player_display = [colored_card(v, s) for v, s in player_hand]

        print("🧑‍💼 Dealer's Hand: " + " ".join(dealer_display))
        if not hide_dealer:
            print(f"Dealer Total: {calculate_total(dealer_hand)}")
        print("🙋 Your Hand:    " + " ".join(player_display))
        print(f"Your Total: {calculate_total(player_hand)}")
        print("═" * 50)

    # --- Initialize hands ---
    player_hand = [draw_card(), draw_card()]
    dealer_hand = [draw_card(), draw_card()]

    display_hands(player_hand, dealer_hand, hide_dealer=True)

    # --- Player turn ---
    while True:
        choice = input("Hit (H), Stand (S), or Quit (Q): ").strip().lower()
        if choice == "q":
            print("Leaving Blackjack table...")
            time.sleep(0.8)
            return
        elif choice == "h":
            player_hand.append(draw_card())
            display_hands(player_hand, dealer_hand, hide_dealer=True)
            if calculate_total(player_hand) > 21:
                loss = -bet
                balance += loss
                session_profit += loss
                print(f"{RED}💥 Bust! You lose {format_money(bet)}.{RESET}")
                vegas_record_result(bet, loss)
                break
        elif choice == "s":
            break
        else:
            print("Please enter H, S, or Q.")

    if calculate_total(player_hand) <= 21:
        # --- Dealer turn ---
        print("\n🧑‍💼 Dealer reveals their hand...")
        time.sleep(1.2)
        display_hands(player_hand, dealer_hand, hide_dealer=False)
        while calculate_total(dealer_hand) < 17:
            print("Dealer hits...")
            time.sleep(1.2)
            dealer_hand.append(draw_card())
            display_hands(player_hand, dealer_hand, hide_dealer=False)

        player_total = calculate_total(player_hand)
        dealer_total = calculate_total(dealer_hand)

        # --- Outcome ---
        if dealer_total > 21:
            win = bet
            balance += win
            session_profit += win
            print(f"{GREEN}🎉 Dealer busts! You win {format_money(win)}!{RESET}")
            vegas_record_result(bet, win)
        elif player_total > dealer_total:
            win = bet
            balance += win
            session_profit += win
            print(f"{GREEN}🏆 You win {format_money(win)}!{RESET}")
            vegas_record_result(bet, win)
        elif player_total < dealer_total:
            loss = -bet
            balance += loss
            session_profit += loss
            print(f"{RED}😢 Dealer wins. You lose {format_money(bet)}.{RESET}")
            vegas_record_result(bet, loss)
        else:
            print(f"{YELLOW}🤝 Push (tie). Your bet is returned.{RESET}")
            vegas_record_result(bet, 0)

    # --- End-of-round summary ---
    print("\n" + "═" * 50)
    if session_profit > 0:
        print(f"{GREEN}🏁 Round Profit: +{format_money(session_profit)}{RESET}")
    elif session_profit < 0:
        print(f"{RED}🏁 Round Loss: {format_money(session_profit)}{RESET}")
    else:
        print(f"{YELLOW}🏁 Round Result: Even (Push){RESET}")
    print(f"💰 Current Balance: {format_money(balance)}")
    print("═" * 50)
    print_portfolio()
    time.sleep(1.5)
    
#----CRAPS---
def vegas_craps():
    """Casino-style Craps game with full table layout, color, and quit option."""
    global balance
    print("\n--- 🎲 Vegas Craps ---")
    bet = vegas_place_bet()
    if not bet:
        return

    # --- Dice + Colors ---
    DIE = ["\u2680", "\u2681", "\u2682", "\u2683", "\u2684", "\u2685"]
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"

    # --- Dice animation ---
    def animate_roll(final_a, final_b, frames=14, base_delay=0.09):
        """Animate rolling dice with emoji."""
        for i in range(frames):
            a = random.choice(DIE)
            b = random.choice(DIE)
            sys.stdout.write(
                "\rRolling the dice... " + random.choice(["🎲", "🎲🎲"]) + "  " + a + " " + b + "   "
            )
            sys.stdout.flush()
            time.sleep(base_delay + (i * 0.01))
        sys.stdout.write("\rResult:  " + DIE[final_a - 1] + " " + DIE[final_b - 1] + "   \n")
        sys.stdout.flush()
        time.sleep(0.4)

    def roll_dice():
        """Return two dice and total."""
        a, b = random.randint(1, 6), random.randint(1, 6)
        animate_roll(a, b)
        return a, b, a + b

    # --- Casino table intro ---
    os.system("cls" if os.name == "nt" else "clear")
    print("🎲 WELCOME TO THE VEGAS CRAPS TABLE 🎲")
    print("──────────────────────────────────────────────")
    print(f"Table Minimum Bet: ${VEGAS_TABLE_MIN:,}")
    print(f"Your Bet: {format_money(bet)} | Balance: {format_money(balance)}")
    print("──────────────────────────────────────────────")
    print(f"{CYAN}Pass Line Bet is ACTIVE!{RESET}")
    print(f"Hit ENTER to roll or 'Q' to leave the table.")
    print("──────────────────────────────────────────────")

    # --- Come-out roll ---
    choice = input().strip().lower()
    if choice == "q":
        print("Leaving Craps table...")
        time.sleep(0.8)
        return

    a, b, total = roll_dice()
    print(f"You rolled {a} + {b} = {total}")

    # --- Instant results on come-out roll ---
    if total in (7, 11):
        balance += bet
        print(f"{GREEN}Natural! You win {format_money(bet)}!{RESET}")
        vegas_record_result(bet, bet)
        print_portfolio()
        return
    elif total in (2, 3, 12):
        balance -= bet
        print(f"{RED}Craps! {total}! House wins! You lose {format_money(bet)}.{RESET}")
        vegas_record_result(bet, -bet)
        print_portfolio()
        return

    # --- Point established ---
    point = total
    print(f"{YELLOW}🔸 Point is set to {point}! Roll {point} before a 7 to win.{RESET}")
    time.sleep(1.0)

    while True:
        choice = input("Press ENTER to roll or 'Q' to quit: ").strip().lower()
        if choice == "q":
            print("Leaving Craps table...")
            time.sleep(0.8)
            return

        a, b, total = roll_dice()
        print(f"You rolled {a} + {b} = {total}")

        if total == point:
            balance += bet
            print(f"{GREEN}🏆 You hit your point {point}! You win {format_money(bet)}!{RESET}")
            vegas_record_result(bet, bet)
            print_portfolio()
            return
        elif total == 7:
            balance -= bet
            print(f"{RED}💀 Seven out! You lose {format_money(bet)}.{RESET}")
            vegas_record_result(bet, -bet)
            print_portfolio()
            return
        else:
            print(f"{CYAN}No result — keep rolling for {point}.{RESET}")
            time.sleep(0.6)

#plinko------------------------------
def vegas_plinko():
    """Plinko ball drop with static pegs, aligned prize boxes and correct landing."""
    global balance
    print("\n--- 🟡 Plinko Drop ---")
    print("Press ENTER to drop a ball or 'Q' to quit back to Vegas Hub.")
    bet = vegas_place_bet()
    if not bet:
        return

    if balance < bet:
        print("❌ Not enough balance for even one ball.")
        return

    # --- Board / slot configuration ---
    multipliers = [5.0,10.0,1.5,2.5,0.2,1.0,0.5,0.25,0,0,0.25,0.5,1.0,0.2,2.5,1.5,10.0,5.0]
    slots = len(multipliers)
    cell_width = 5            # characters per slot cell (must be odd to center nicely)
    board_width = slots * cell_width
    height = 14               # number of rows (peg rows before slots)
    peg_char = "⚪"
    ball_char = "🟡"

    # --- Precompute static peg centers (x positions) per row ---
    # Pegs are placed at the center of each cell, alternating offset per row
    peg_centers = []
    for row in range(height - 1):
        centers = []
        # alternate pattern: even rows have pegs centered in every cell,
        # odd rows offset half-cell to create staggered pegs.
        if row % 2 == 0:
            for c in range(slots):
                cx = c * cell_width + cell_width // 2
                centers.append(cx)
        else:
            for c in range(slots - 1):
                # offset between cells: middle between two cell centers
                cx = (c * cell_width + cell_width // 2) + (cell_width // 2)
                centers.append(cx)
        peg_centers.append(centers)

    # --- Helpers to render board and ball ---
    def print_board(ball_col=None, ball_row=None):
        """Render the plinko board with perfectly centered prize boxes."""
        os.system("cls" if os.name == "nt" else "clear")
        print(f"💵 Bet per ball: {format_money(bet)} | Balance: {format_money(balance)}")
        print("Press ENTER to drop another ball or 'Q' to quit.\n")

        # Draw peg rows
        for r in range(height):
            line = [" "] * board_width
            if r < len(peg_centers):
                for cx in peg_centers[r]:
                    if 0 <= cx < board_width:
                        line[cx] = peg_char
            if ball_col is not None and ball_row == r:
                bx = ball_col * cell_width + cell_width // 2
                if 0 <= bx < board_width:
                    line[bx] = ball_char
            print("".join(line))

        # ╔ top ╦ border ═
        top = "╔" + ("═" * cell_width + "╦") * (slots - 1) + "═" * cell_width + "╗"
        bottom = "╚" + ("═" * cell_width + "╩") * (slots - 1) + "═" * cell_width + "╝"
        print(top)

        # │ Center labels inside boxes │
        label_row = ""
        for i, m in enumerate(multipliers):
            label = f"{m:.1f}x"
            # Use centered text inside each cell with box lines
            if i < slots - 1:
                label_row += "│" + label.center(cell_width)
            else:
                label_row += "│" + label.center(cell_width) + "│"
        print(label_row)
        print(bottom)


    def drop_ball():
        """Simulate one ball drop using column indices (ensures alignment)."""
        global balance
        if balance < bet:
            print("❌ Not enough balance to drop another ball.")
            time.sleep(1.0)
            return None

        # Deduct bet up front
        balance -= bet

        # Start column in center
        col = slots // 2

        # For each row, show animation and possibly deflect at peg rows
        for r in range(height - 1):
            # render ball at current column and row
            print_board(ball_col=col, ball_row=r)
            # delay increases slightly to give a falling feeling
            time.sleep(0.10 + (r * 0.01))

            # if this row has peg centers that align with the current column center,
            # the ball hits a peg and deflects left or right
            peg_row_centers = peg_centers[r]
            # determine x center for this column
            col_center_x = col * cell_width + cell_width // 2
            # if ball center is at (one of peg centers) OR if the peg row is staggered,
            # we approximate a peg hit if nearest peg center distance <= (cell_width//2)
            hit = False
            for pcx in peg_row_centers:
                if abs(pcx - col_center_x) <= (cell_width // 2):
                    hit = True
                    break

            if hit:
                # prefer small bias toward center to prevent runaway extremes
                move = random.choice([-1, 1])
                # small chance to stay straight (no move)
                if random.random() < 0.12:
                    move = 0
                col += move
                # clamp to valid columns
                col = max(0, min(slots - 1, col))

        # Final resting column = slot index
        slot_index = int(col)
        # Jackpot override (rare)
        if random.random() < 0.01:
            mult = 100.0
            print("\n💥 JACKPOT! The ball hit the rare 100× slot! 💥")
        else:
            mult = multipliers[slot_index]

        win = bet * mult
        balance += win
        # record net (winnings - bet) because we already deducted bet
        vegas_record_result(bet, win - bet)
        print_board(ball_col=slot_index, ball_row=height - 1)
        print(f"\n🎯 Landed in {mult}x slot! You won {format_money(win)}!")
        print_portfolio()
        time.sleep(1.4)

    # --- Main loop ---
    while True:
        print_board()
        choice = input().strip().lower()
        if choice == "q":
            print("Leaving Plinko table...")
            time.sleep(0.6)
            return
        else:
            drop_ball()

    
#stackem game -----------------------------------
def vegas_stack_em():
    """Stack 'Em arcade-style game 🟦🟩 with 15 levels and payout milestones."""
    global balance
    print("\n--- 🧱 Stack 'Em ---")
    bet = vegas_place_bet()
    if not bet:
        return

    width = 5
    max_width = width
    levels = 15
    pos = 0
    direction = 1
    speed = 0.12
    tower = []  # store positions of placed blocks
    symbols = ["🟦", "🟩"]


    print("\nPress ENTER to stop the moving block each level!")
    time.sleep(2)

    for level in range(levels):
        color = symbols[level % 2]
        moving_width = width
        track_len = 20
        pos = 0
        direction = 1

        prev_start, prev_end = (tower[-1] if tower else (0, track_len))

        while True:
            # draw tower so far
            sys.stdout.write("\033[H\033[J")  # clear screen
            print(f"🏗️ Stack 'Em  —  Level {level + 1}/{levels} | Bet: {format_money(bet)}")
            print("Press ENTER to stop the moving block!\n")

            # draw current tower
            for y in range(len(tower)):
                s, e = tower[y]
                row = " " * s + (symbols[y % 2] * (e - s)) + " " * (track_len - e)
                print(row)
            # draw moving block
            row = " " * pos + (color * moving_width) + " " * (track_len - (pos + moving_width))
            print(row)

            time.sleep(speed)
            pos += direction
            if pos + moving_width >= track_len or pos <= 0:
                direction *= -1

            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                input()  # catch Enter press
                break

        # Determine overlap with previous
        start = max(pos, prev_start)
        end = min(pos + moving_width, prev_end)
        overlap = end - start
        if overlap <= 0:
            print("❌ No overlap! The stack fell!")
            balance -= bet
            vegas_record_result(bet, -bet)
            print_portfolio()
            return
        else:
            tower.append((start, end))
            width = overlap
            # Increase speed
            speed = max(0.03, speed * 0.9)

        # Milestone payouts
        if level + 1 == 8:
            bonus = bet * 2
            balance += bonus
            print(f"\n🎉 Middle Milestone reached! +{format_money(bonus)}!")
            time.sleep(1)
        elif level + 1 == levels:
            bonus = bet * 10
            balance += bonus
            print(f"\n🏆 TOP OF THE TOWER! +{format_money(bonus)} JACKPOT!")
            time.sleep(2)
            vegas_record_result(bet, bet * 12.5)  # total winnings including earlier bonuses
            print_portfolio()
            return

    vegas_record_result(bet, payout)
    print_portfolio()


# -------------------------
# --- END VEGAS CODE
# -------------------------

#--black market----------------------
def black_market_menu():
    """Main black market hub."""
    global black_market_inventory, black_market_orders
    while True:
        print("\n=== ⚠️ BLACK MARKET ⚠️ ===")
        print(f"Cash: {format_money(balance)} | Day: {days_passed}")
        print("1) Browse & Buy items")
        print("2) View your black market inventory")
        print("3) List an item for sale (350% return, 10 days to fulfill)")
        print("4) View active orders")
        print("5) Buy Fake ID")
        print("6) Heist Menu")
        print("Q) Quit")
        ch = input("Select: ").strip().lower()
        if ch == "1":
            buy_black_market_item()
        elif ch == "2":
            view_black_market_inventory()
        elif ch == "3":
            list_black_market_sale()
        elif ch == "5":
            buy_fake_id()
        elif ch == "6":
            heist_menu()
        elif ch == "4":
            view_black_market_orders()
        elif ch == "q":
            print("Leaving Black Market...")
            time.sleep(0.6)
            return
        else:
            print("Invalid option.")

def buy_fake_id():
    """Buy a Fake ID to transact on the black market.

    Now respects a confiscation lock: if fake_id_locked_until > days_passed the player
    cannot purchase a new Fake ID until that day.
    """
    global balance, player_has_fake_id, FAKE_ID_COST, fake_id_locked_until, days_passed

    print("\n--- 🪪 Buy Fake ID ---")
    print(f"Current Fake ID cost: {format_money(FAKE_ID_COST)}")

    # Already have one
    if player_has_fake_id:
        print("You already have a valid Fake ID.")
        return

    # Locked due to confiscation: tell the player how many days remain
    if fake_id_locked_until and days_passed < fake_id_locked_until:
        days_left = fake_id_locked_until - days_passed
        print(f"⚠️ Fake ID purchases are restricted. You can't buy a replacement for another {days_left} in-game day(s).")
        return

    confirm = input(f"Buy Fake ID for {format_money(FAKE_ID_COST)}? (y/n): ").strip().lower()
    if confirm != "y":
        print("Fake ID purchase cancelled.")
        return
    if balance < FAKE_ID_COST:
        print("Not enough cash to buy a Fake ID.")
        return

    balance -= FAKE_ID_COST
    player_has_fake_id = True
    # Clear any previous lock if buying legitimately
    fake_id_locked_until = 0

    log_trade("FAKEID BUY", "Fake ID", 1, FAKE_ID_COST, result=f"Bought Fake ID")

    # bump the price AFTER purchase so subsequent purchases cost more
    try:
        FAKE_ID_COST = round(FAKE_ID_COST * FAKE_ID_PURCHASE_INCREASE, 2)
    except Exception:
        FAKE_ID_COST = round(FAKE_ID_COST * 1.15, 2)

    save_game()
    print(f"✅ You purchased a Fake ID. You can now buy/list items on the Black Market.")
    print(f"🔼 Note: The Fake ID price has increased to {format_money(FAKE_ID_COST)} for the next purchase.")



def process_black_market_orders():
    """Processes black market orders with risk compounding based on quantity."""
    global black_market_orders, balance, player_has_fake_id, black_market_history

    if 'player_has_fake_id' not in globals():
        player_has_fake_id = False

    if not black_market_orders:
        return

    completed_orders = []

    for order in list(black_market_orders):
        # decrement remaining days
        order["days_left"] = max(0, order.get("days_left", 0) - 1)
        if order["days_left"] > 0:
            continue

        item_name = order.get("item", "Unknown Item")

        # --- Safe lookup with defaults ---
        if "BLACK_MARKET_ITEMS" not in globals():
            print("⚠️ Missing black market catalog; skipping processing.")
            continue

        item_data = BLACK_MARKET_ITEMS.get(item_name)
        if not item_data:
            print(f"⚠️ '{item_name}' not found in catalog — using default values.")
            item_data = {"price": 1000, "risk": 0.25, "days": 10}
            BLACK_MARKET_ITEMS[item_name] = item_data

        base_price = float(item_data.get("price", 1000))
        base_risk = float(item_data.get("risk", 0.25))
        qty = int(order.get("qty", 1))

        # --- Adjust risk by quantity (compound probability) ---
        # Overall confiscation chance = 1 - (1 - base_risk)^qty
        combined_risk = 1 - ((1 - base_risk) ** qty)

        # Fake ID lowers total risk by 25 %
        if player_has_fake_id:
            combined_risk *= 0.75

        # --- Roll for outcome ---
        roll = random.random()

        if roll < combined_risk:
            # Confiscated
            print(f"\n🚨 Authorities confiscated your {qty}x {item_name} shipment!")
            if player_has_fake_id:
                print("🪪 Your fake ID was seized in the bust.")
                player_has_fake_id = False

            black_market_history.append({
                "item": item_name,
                "qty": qty,
                "result": f"Confiscated (roll {roll:.2f} < risk {combined_risk:.2f})",
                "profit": 0,
                "day_completed": days_passed
            })
        else:
            # Successful sale
            payout = qty * base_price * 2.5  # 250 % markup
            balance += payout
            print(f"\n💰 Sold {qty}x {item_name} for ${payout:,.2f} "
                  f"(roll {roll:.2f} ≥ risk {combined_risk:.2f})")

            black_market_history.append({
                "item": item_name,
                "qty": qty,
                "result": f"Sold (safe {roll:.2f} ≥ {combined_risk:.2f})",
                "profit": payout,
                "day_completed": days_passed
            })

        completed_orders.append(order)

    # remove processed orders
    for order in completed_orders:
        if order in black_market_orders:
            black_market_orders.remove(order)

    # auto-save after processing
    if "save_game" in globals():
        try:
            save_game()
        except Exception:
            pass


#---Blcak market Menu----

def normalize_heist_flags():
    """Ensure every wanted flag has the canonical keys used elsewhere."""
    global heist_wanted_flags, days_passed, HEIST_WANTED_DAYS

    for f in heist_wanted_flags:
        # ensure days_left exists
        if "days_left" not in f:
            f["days_left"] = HEIST_WANTED_DAYS
        # ensure total_catch exists (default conservative 30%)
        if "total_catch" not in f:
            f["total_catch"] = min(1.0, 0.30)
        # ensure created_day exists
        if "created_day" not in f:
            f["created_day"] = days_passed
        # ensure daily_catch_p exists and is consistent with total_catch/days_left
        if "daily_catch_p" not in f or (f.get("days_left", HEIST_WANTED_DAYS) > 0 and f.get("total_catch", 0) > 0):
            total = f.get("total_catch", 0.30)
            days = f.get("days_left", HEIST_WANTED_DAYS)
            # Avoid division by zero
            days = max(days, HEIST_WANTED_DAYS)
            f["daily_catch_p"] = 1 - (1 - total) ** (1.0 / days)


def buy_black_market_item():
    """Buy a quantity of a chosen black-market item."""
    global balance, black_market_inventory, player_has_fake_id
    print("\n--- Browse Black Market ---")

    # require Fake ID to transact
    if not player_has_fake_id:
        print("⚠️ You need a valid Fake ID to buy from the Black Market.")
        want = input("Buy a Fake ID now? (y/n): ").strip().lower()
        if want == "y":
            buy_fake_id()
            if not player_has_fake_id:
                return
        else:
            return
    for i, (name, data) in enumerate(BLACK_MARKET_ITEMS.items(), start=1):
        print(f"{i}) {name:15} | Price: {format_money(data['price'])} | Risk factor: {int(data['risk']*100)}%")
    choice = input("Enter item number to buy or press Enter to cancel: ").strip()
    if not choice:
        return
    try:
        idx = int(choice) - 1
        item = list(BLACK_MARKET_ITEMS.keys())[idx]
    except Exception:
        print("Invalid selection.")
        return
    try:
        qty = int(input(f"How many {item} do you want to buy? (integer): "))
        if qty <= 0:
            print("Enter a positive integer.")
            return
    except ValueError:
        print("Invalid quantity.")
        return
    total_cost = BLACK_MARKET_ITEMS[item]["price"] * qty
    if total_cost > balance:
        print("Not enough cash.")
        return
    balance -= total_cost
    black_market_inventory[item] = black_market_inventory.get(item, 0) + qty
    log_trade("BM BUY", item, qty, BLACK_MARKET_ITEMS[item]["price"], result=f"Paid {format_money(total_cost)}")
    print(f"Purchased {qty} x {item} for {format_money(total_cost)}. Items available to list for sale.")
    save_game()


def view_black_market_inventory():
    """Show player's black market goods and quantities."""
    print("\n--- Your Black Market Inventory ---")
    if not black_market_inventory:
        print("You hold no black market items.")
        return
    for item, qty in black_market_inventory.items():
        print(f"{item:<18} | Qty: {qty} | Buy price: {format_money(BLACK_MARKET_ITEMS[item]['price'])}")
    print("-----------------------------------")


def list_black_market_sale():
    """List owned items for sale at fixed 2.5x price; order fulfills after 10 days with confiscation risk."""
    global black_market_inventory, black_market_orders
    if not black_market_inventory:
        print("\nYou have no items to list.")
        return
    print("\n--- List Item for Sale (2.5x payout, 10 days) ---")
    for i, (item, qty) in enumerate(black_market_inventory.items(), start=1):
        base = BLACK_MARKET_ITEMS[item]["price"]
        print(f"{i}) {item:18} | You: {qty} | Will sell at: {format_money(base * BLACK_MARKET_SALE_MULTIPLIER)} each")
    choice = input("Select item number to list or press Enter to cancel: ").strip()
    if not choice:
        return
    try:
        idx = int(choice) - 1
        item = list(black_market_inventory.keys())[idx]
    except Exception:
        print("Invalid selection.")
        return
    try:
        q = int(input(f"Quantity to list (you have {black_market_inventory[item]}): "))
        if q <= 0 or q > black_market_inventory[item]:
            print("Invalid quantity.")
            return
    except ValueError:
        print("Invalid quantity.")
        return
        # require Fake ID to list / sell
    if not player_has_fake_id:
        print("⚠️ You need a valid Fake ID to list items for sale on the Black Market.")
        want = input("Buy a Fake ID now? (y/n): ").strip().lower()
        if want == "y":
            buy_fake_id()
            if not player_has_fake_id:
                return
        else:
            return


    # Reserve the items (remove from inventory immediately and create order)
    black_market_inventory[item] -= q
    if black_market_inventory[item] == 0:
        del black_market_inventory[item]

    order = {
        "item": item,
        "qty": q,
        "price_per_unit": BLACK_MARKET_ITEMS[item]["price"] * BLACK_MARKET_SALE_MULTIPLIER,
        "days_left": BLACK_MARKET_FULFILL_DAYS,
        "confiscation_risk": BLACK_MARKET_ITEMS[item]["risk"]
    }
    black_market_orders.append(order)
    log_trade("BM LIST", item, q, order["price_per_unit"], result=f"Listing for {BLACK_MARKET_FULFILL_DAYS} days")
    print(f"Listed {q} x {item} for sale. Order will attempt fulfillment in {BLACK_MARKET_FULFILL_DAYS} days.")
    save_game()


def view_black_market_orders():
    """Show active and past black-market orders."""
    print("\n--- 🕵️ Black Market Orders ---")

    # --- Active Orders ---
    if black_market_orders:
        print("\n📦 Active Orders:")
        for i, o in enumerate(black_market_orders, start=1):
            print(
                f"{i}) {o['qty']}x {o['item']} | ${o['price_per_unit']:.2f}/ea "
                f"| Days left: {o['days_left']} | Risk: {int(o['confiscation_risk']*100)}%"
            )
    else:
        print("\n📦 No active orders.")

    # --- Past Orders / History ---
    if black_market_history:
        print("\n📜 Past Orders:")
        for i, o in enumerate(black_market_history[-15:], start=1):  # show last 15
            result_color = "\033[92m" if "Successful" in o["result"] else "\033[91m"
            reset = "\033[0m"
            print(
                f"{i:>2}) {o['qty']}x {o['item']:<18} | "
                f"{result_color}{o['result']:<25}{reset} | "
                f"Profit: {format_money(o['profit']):<10} | "
                f"Completed Day: {o['day_completed']}"
            )
    else:
        print("\n📜 No past orders yet.")

    print("─────────────────────────────────────────────────────────────")
    
#heist menu-------------------------------------    
def heist_menu():
    """Heist hub under Black Market."""
    while True:
        print("\n=== 🏴‍☠️   HEIST MENU   ☠️ 🏴‍===")
        print(f"Cash: {format_money(balance)} | Bank: {format_money(bank_balance)} | Day: {days_passed}")
        print("\n1) 💰  Bank Heist")
        print("Requires - Fake ID, Passport, Credit Card (cloned), Spare Drill Bit, Hacking LapTop")
        print("Drill, Hacking Software, Inside Man Fee,")
        print("\n2) 👨🏻‍💻   Hacking Heist ")
        print("Requires - Hacking Software, Inside Man Fee, Hacking LapTop, Credit Card (cloned)")
        print("\n3) 🏛️  Prison Break Heist")
        print("Requires - Fake ID, Spare Drill Bit, Drill, Get Away Car,")
        print("Hacking Software, Hacking Laptop, Guard Uniform, Inside Man Fee")
        print("\nI) View Heist Inventory (equipment you own)")
        print("B) Buy Heist Equipment (from catalog)")
        print("V) View Wanted Flags / Heist History")
        print("Q) Back to Black Market")
        ch = input("Choose: ").strip().lower()
        if ch == "1":
            start_bank_heist()
        elif ch == "2":
            start_hacking_heist()
        elif ch == "3":
            heist_prison_break()
        elif ch == "i":
            view_heist_inventory()
        elif ch == "b":
            buy_heist_equipment()
        elif ch == "v":
            view_heist_status()
        elif ch == "q":
            return
        else:
            print("Invalid option.")
            
def buy_heist_equipment():
    """Buy equipment for heists (adds into heist_inventory)."""
    global balance, heist_inventory, buy_heist_equipment, heist_menu
    print("\n--- Heist Equipment Store ---")
    print(f"Cash: {format_money(balance)} | Bank: {format_money(bank_balance)} | Day: {days_passed}")
    items = list(HEIST_EQUIPMENT.items())
    for i, (name, data) in enumerate(items, start=1):
        print(f"{i}) {name:20} | Price: {format_money(data['price'])}")
    choice = input("Select item number to buy or Enter to cancel: ").strip()
    if not choice:
        return
    try:
        idx = int(choice) - 1
        name = items[idx][0]
    except Exception:
        print("Invalid choice.")
        return
    price = HEIST_EQUIPMENT[name]["price"]
    if balance < price:
        print("Not enough cash.")
        return
    qty = 1
    balance -= price
    heist_inventory[name] = heist_inventory.get(name, 0) + qty
    log_trade("HEIST BUY", name, qty, price, result=f"Bought {name}")
    save_game()
    print(f"Purchased {name} for {format_money(price)}.")
    buy_heist_equipment()

def view_heist_inventory():
    """Show owned heist equipment."""
    print("\n--- Your Heist Equipment ---")
    if not heist_inventory:
        print("You own no heist equipment.")
        return
    for name, qty in heist_inventory.items():
        print(f"{name:25} | Qty: {qty}")

#heist minigams--------------------------------------

def _play_hack_minigame():
    """🧠 Hacking mini-game with memory + timed command-entry challenge.
    Fix: wrong_attempts is computed dynamically from current typed vs command,
    so correcting a character reduces the mistake count immediately.
    Returns (success: bool, multiplier: float)."""
    import random, os, sys, time, termios, tty, string

    def get_key():
        """Capture a single key press (raw, no Enter). Maps arrow keys to wasd."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == '\x1b':  # possible arrow sequence
                ch2 = sys.stdin.read(1)
                ch3 = sys.stdin.read(1)
                if ch2 == '[':
                    if ch3 == 'A':
                        return 'w'
                    if ch3 == 'B':
                        return 's'
                    if ch3 == 'C':
                        return 'd'
                    if ch3 == 'D':
                        return 'a'
                # anything else - return nothing sensible
                return ''
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def colored(text, code):
        return f"\033[{code}m{text}\033[0m"

    # --- Stage 1: Memory code (3 tries, extra view time) ---
    os.system("cls" if os.name == "nt" else "clear")
    print("💻 HACKING INITIATED... Memory sequence incoming.")
    time.sleep(0.8)

    code = "".join(random.choice("0123456789ABCDEF!@#$%^&*") for _ in range(6))
    print(f"\n🔢 Memorize this code: {colored(code, '93')}")
    print("You have 7 seconds to memorize it.")
    time.sleep(7)
    os.system("cls" if os.name == "nt" else "clear")

    print("🧠 Enter the code you just saw. You have 3 attempts.")
    success = False
    for attempt in range(1, 4):
        guess = input(f"Attempt {attempt}/3 >>> ").strip().upper()
        if guess == code:
            print(colored("✅ Correct.", "92"))
            success = True
            break
        else:
            print(colored("❌ Incorrect.", "91"))
            if attempt < 3:
                time.sleep(0.8)
    if not success:
        print(colored("💀 All attempts failed. Access denied.", "91"))
        return False, 0.0

    time.sleep(0.8)
    print("\nProceeding to command interface...")
    time.sleep(1.0)

    # --- Stage 2: Command Entry Challenge ---
    def random_command():
        chars = string.ascii_lowercase + string.digits + "/"
        length = random.randint(10, 15)
        return "".join(random.choice(chars) for _ in range(length))

    rounds = 3
    for rnd in range(1, rounds + 1):
        command = random_command()
        typed = ""
        round_start = time.time()
        TIME_LIMIT = 30.0

        while True:
            elapsed = time.time() - round_start
            remaining = TIME_LIMIT - elapsed
            if remaining <= 0:
                print(colored("\n⏰ Time's up! You failed to enter the command.", "91"))
                return False, 0.0

            # compute current mismatches dynamically
            mismatches = 0
            for i in range(len(typed)):
                if i >= len(command) or typed[i] != command[i]:
                    mismatches += 1

            # draw the screen
            os.system("cls" if os.name == "nt" else "clear")
            print(f"💻 Command Entry — Round {rnd}/{rounds}")
            print(f"⏳ Time left: {remaining:4.1f}s   ❌ Current mismatches: {mismatches}/3")
            print()
            # render the command with colors:
            display = []
            for i, ch in enumerate(command):
                if i < len(typed):
                    # typed char: green if correct at this position, red otherwise
                    if typed[i] == ch:
                        display.append(colored(ch, "92"))  # green
                    else:
                        display.append(colored(ch, "91"))  # red
                else:
                    display.append(colored(ch, "91"))  # not yet typed -> red
            print("".join(display))
            print()
            print("Type the command exactly ( ' - ' to abort). Use Backspace to correct.")
            sys.stdout.flush()

            # fail if too many current mismatches
            if mismatches > 3:
                print(colored("\n❌ Too many mistakes. Hack failed.", "91"))
                return False, 0.0

            # get next keypress
            key = get_key()
            if not key:
                continue

            # handle quit
            if key.lower() == '-':
                print(colored("\n❌ You aborted the hack.", "91"))
                return False, 0.0

            # handle backspace (both DEL and BS)
            if key in ('\x7f', '\b'):
                if typed:
                    typed = typed[:-1]
                continue

            # ignore control chars and non-printable except common ones
            if ord(key) < 15:
                continue

            # prevent typing beyond command length
            if len(typed) >= len(command):
                # extra keystrokes ignored (prompt user to backspace)
                continue

            # append the new character (do not force case; commands are lowercase)
            typed += key

            # if current typed exactly matches command -> success this round
            if typed == command:
                os.system("cls" if os.name == "nt" else "clear")
                print(colored("\n✅ Command accepted!", "92"))
                time.sleep(0.9)
                break

            # otherwise loop continues; mismatches will be recalculated next iteration

    # if all rounds passed
    print(colored("\n🎉 All commands entered successfully! Hack complete.", "92"))
    return True, 2.0

def _play_drill_minigame():
    """Snake Drill mini-game: grow your drill 5 times to win."""
    height = 20
    width = 35
    lives = 3
    target_growth = 3
    growth = 0

    # starting snake position
    snake = [(width // 2, height // 2)]
    direction = (1, 0)  # moving right
    food = None

    print("\n🐍 DRILL MINI-GAME: 'Snake Drill'")
    print("Use arrow keys or WASD to move.")
    print(f"Goal: Eat {target_growth} 💎 vault cores without crashing.")
    print("Press Q to quit anytime.")
    time.sleep(2)

    # setup raw mode for instant input
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)

    def get_input(timeout=0.1):
        dr, _, _ = select.select([sys.stdin], [], [], timeout)
        if dr:
            return sys.stdin.read(1)
        return None

    def place_food():
        while True:
            pos = (random.randint(1, width - 2), random.randint(1, height - 2))
            if pos not in snake:
                return pos

    food = place_food()

    try:
        while True:
            # move snake
            head_x, head_y = snake[0]
            new_head = (head_x + direction[0], head_y + direction[1])

            # collision detection
            if (
                new_head[0] <= 0 or new_head[0] >= width - 1 or
                new_head[1] <= 0 or new_head[1] >= height - 1 or
                new_head in snake
            ):
                lives -= 1
                print(f"💥 You crashed! Lives left: {lives}")
                if lives <= 0:
                    print("❌ Drill exploded! You failed the vault drilling.")
                    return False
                # reset small snake
                snake = [(width // 2, height // 2)]
                direction = (1, 0)
                food = place_food()
                growth = 0
                time.sleep(1)
                continue

            # insert new head
            snake.insert(0, new_head)

            # check if food eaten
            if new_head == food:
                growth += 1
                food = place_food()
                if growth >= target_growth:
                    print("\n🏆 You drilled through the vault! Success!")
                    return True
            else:
                snake.pop()  # remove tail (normal move)

            # draw frame
            print("\033c", end="")  # clear
            print(f"Length: {len(snake)} | Growth: {growth}/{target_growth} | Lives: {lives}")
            for y in range(height):
                line = ""
                for x in range(width):
                    if (x, y) in snake:
                        line += "🪛" if (x, y) == snake[0] else "■"
                    elif (x, y) == food:
                        line += "💎"
                    elif x == 0 or x == width - 1 or y == 0 or y == height - 1:
                        line += "█"
                    else:
                        line += " "
                print(line)
            print("Use ↑ ↓ ← → or WASD to steer. Q to quit.")

            # handle input
            ch = get_input(0.15)
            if ch:
                ch = ch.lower()
                if ch == "q":
                    print("You aborted the drilling.")
                    return False
                elif ch in ["w", "k", "A"]:  # up
                    direction = (0, -1)
                elif ch in ["s", "j", "B"]:  # down
                    direction = (0, 1)
                elif ch in ["a", "h", "D"]:  # left
                    direction = (-1, 0)
                elif ch in ["d", "l", "C"]:  # right
                    direction = (1, 0)

    finally:
        # restore terminal mode
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def _play_portfolio_hack_minigame():
    """Abstract portfolio hack: guessing game. Returns True on success."""
    print("\n--- Portfolio Infiltration Mini-Game ---")
    target = random.randint(1, 10)
    attempts = 4
    print(f"Guess the target number between 1 and 10 (you have {attempts} attempts).")
    for i in range(attempts):
        try:
            g = int(input(f"Guess #{i+1}: "))
        except ValueError:
            print("Invalid.")
            continue
        if g == target:
            print("Infiltration success.")
            return True
        if abs(g - target) <= 3:
            print("Close...")
        if abs(g - target) <= 2:
            print("Closer...")
        if abs(g - target) <= 1:
            print("Damn thats close...")
        if abs(g - target) <= 5:
            print("Somewhere around this number...")
        else:
            print("Nope.")
    print("Infiltration failed.")
    return False

def _play_steal_money_minigame():
    """💸 2048-style mini-game for stealing money. Win by reaching a tile of 100."""
    import random, os, sys, termios, tty

    def get_key():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == '\x1b':  # arrow key prefix
                sys.stdin.read(1)
                ch2 = sys.stdin.read(1)
                if ch2 == 'A': return 'w'
                if ch2 == 'B': return 's'
                if ch2 == 'C': return 'd'
                if ch2 == 'D': return 'a'
            return ch.lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def print_board(board, score):
        os.system("cls" if os.name == "nt" else "clear")
        print("\n💸 Money Steal — Reach tile 128 to win!\n")
        print(f"Score: {score}")
        print("╔════╦════╦════╦════╗")
        for row in board:
            print("║" + "║".join(f"{x:^4}" if x else "    " for x in row) + "║")
            print("╠════╬════╬════╬════╣")
        print("\033[F", end="")  # clean last border line
        print("╚════╩════╩════╩════╝")
        print("Use W/A/S/D or arrow keys to move. Q to quit.\n")

    def add_tile(board):
        """Add a random new tile (2 or 5 or 10) to an empty cell."""
        empty = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]
        if not empty:
            return
        r, c = random.choice(empty)
        board[r][c] = random.choice([2, 4])

    def compress_and_merge(line):
        new_line = [x for x in line if x != 0]
        merged = []
        skip = False
        for i in range(len(new_line)):
            if skip:
                skip = False
                continue
            if i + 1 < len(new_line) and new_line[i] == new_line[i + 1]:
                merged.append(new_line[i] * 2)
                skip = True
            else:
                merged.append(new_line[i])
        merged += [0] * (4 - len(merged))
        return merged

    def move(board, direction):
        changed = False
        if direction in ['a', 'd']:
            for r in range(4):
                line = board[r][:]
                if direction == 'd':
                    line = line[::-1]
                new_line = compress_and_merge(line)
                if direction == 'd':
                    new_line = new_line[::-1]
                if new_line != board[r]:
                    board[r] = new_line
                    changed = True
        elif direction in ['w', 's']:
            for c in range(4):
                col = [board[r][c] for r in range(4)]
                if direction == 's':
                    col = col[::-1]
                new_col = compress_and_merge(col)
                if direction == 's':
                    new_col = new_col[::-1]
                for r in range(4):
                    if board[r][c] != new_col[r]:
                        board[r][c] = new_col[r]
                        changed = True
        return changed

    # --- Initialize game ---
    board = [[0]*4 for _ in range(4)]
    score = 0
    # start with exactly 2 tiles of value 2
    for _ in range(2):
        empty = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]
        r, c = random.choice(empty)
        board[r][c] = 2

    while True:
        print_board(board, score)
        if any(128 in row for row in board):
            print("🏆 You reached 128! Successful money steal!")
            return True, 3.0  # success multiplier
        if not any(0 in row for row in board) and not any(
            board[r][c] == board[r][c+1] or board[r][c] == board[r+1][c]
            for r in range(3) for c in range(3)
        ):
            print("❌ No more moves. You failed the extraction.")
            return False, 0.0

        key = get_key()
        if key == 'q':
            print("❌ You gave up the heist.")
            return False, 0.0
        if key in ['w', 'a', 's', 'd']:
            if move(board, key):
                add_tile(board)
                score += 1


def ascii_getaway_minigame():
    """ASCII racing: dodge obstacles while escaping (A/D to move)."""
    import termios, tty, select, sys, os, time, random

    width = 20
    height = 10
    car_x = width // 2
    score = 0
    obstacles = []
    delay = 0.35  # starting frame delay

    # --- Keyboard input setup ---
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)

    try:
        while True:
            os.system("cls" if os.name == "nt" else "clear")
            grid = [[" "] * width for _ in range(height)]

            # Spawn new obstacles randomly
            if random.random() < 0.25:
                obstacles.append([0, random.randint(0, width - 1)])  # [y, x]

            # Move obstacles down
            for o in obstacles:
                o[0] += 1
            obstacles = [o for o in obstacles if o[0] < height]

            # Draw obstacles
            for o in obstacles:
                y, x = o
                if 0 <= y < height and 0 <= x < width:
                    grid[y][x] = "🚔"

            # Draw player car
            grid[height - 1][car_x] = "🚗"

            # Collision detection
            for o in obstacles:
                if o[0] == height - 1 and o[1] == car_x:
                    print("\n💥 You crashed into an obstacle!")
                    time.sleep(1)
                    return False

            # Render screen
            for row in grid:
                print("".join(row))
            print(f"Score: {score}  (Use A/D to move)")

            # --- Real-time keyboard input ---
            dr, _, _ = select.select([sys.stdin], [], [], delay)
            if dr:
                key = sys.stdin.read(1).lower()
                if key == "a":
                    car_x = max(0, car_x - 1)
                elif key == "d":
                    car_x = min(width - 1, car_x + 1)
                elif key == "q":
                    print("\n🏁 You quit the escape.")
                    time.sleep(1)
                    return False

            # Update game state
            score += 0.5
            delay = max(0.005, delay - 0.002)  # gradually speed up

            if score >= 50:
                print("\n🏁 You escaped successfully!")
                time.sleep(1)
                return True

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def breakout_lock_minigame():
    """ASCII Breakout mini-game: destroy ~45% of bricks to break the lock (A/D to move)."""
    import sys, os, time, termios, tty, select, random

    width = 36
    height = 25
    paddle_width = 14
    ball_x, ball_y = width // 2, height - 3
    ball_dx, ball_dy = random.choice([-1, 1]), -1
    paddle_x = width // 2 - paddle_width // 2
    bricks = {(x, y) for x in range(2, width - 2) for y in range(2, 5, 2)}
    total_bricks = len(bricks)
    target_bricks_broken = int(total_bricks * 0.47)  # ✅ Win at 45%
    lives = 3
    frame_delay = 0.08  # ✅ Fixed frame timing

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)

    bricks_broken = 0

    try:
        last_frame = time.time()

        while lives > 0 and bricks_broken < target_bricks_broken:
            # --- Timing control ---
            now = time.time()
            elapsed = now - last_frame
            if elapsed < frame_delay:
                time.sleep(frame_delay - elapsed)
            last_frame = time.time()

            # --- Clear screen ---
            os.system("cls" if os.name == "nt" else "clear")
            print("🔓 BREAKOUT LOCK — A/D to move | Lives:", lives)
            grid = [[" "] * width for _ in range(height)]

            # Draw bricks
            for x, y in bricks:
                if 0 <= y < height and 0 <= x < width:
                    grid[y][x] = "█"

            # Draw paddle
            for i in range(paddle_width):
                px = paddle_x + i
                if 0 <= px < width:
                    grid[height - 1][px] = "_"

            # Draw ball
            if 0 <= ball_y < height and 0 <= ball_x < width:
                grid[ball_y][ball_x] = "●"

            # Print screen
            for row in grid:
                print("".join(row))
            print(f"Bricks broken: {bricks_broken}/{target_bricks_broken}  |  Lives: {lives}")

            # --- Non-blocking input (does not affect timing) ---
            dr, _, _ = select.select([sys.stdin], [], [], 0)
            if dr:
                key = sys.stdin.read(1).lower()
                if key == "a":
                    paddle_x = max(0, paddle_x - 2)
                elif key == "d":
                    paddle_x = min(width - paddle_width, paddle_x + 2)
                elif key == "q":
                    print("\n🏁 You quit the breakout.")
                    time.sleep(1)
                    return False

            # --- Ball movement ---
            ball_x += ball_dx
            ball_y += ball_dy

            # Bounce off walls
            if ball_x <= 0 or ball_x >= width - 1:
                ball_dx *= -1
            if ball_y <= 0:
                ball_dy *= -1

            # Bounce off paddle
            if ball_y == height - 1 and paddle_x <= ball_x <= paddle_x + paddle_width - 1:
                ball_dy = -1
                if random.random() < 0.5:
                    ball_dx = random.choice([-1, 0, 1])

            # Brick collision
            if (ball_x, ball_y) in bricks:
                bricks.remove((ball_x, ball_y))
                bricks_broken += 1
                ball_dy *= -1

            # Ball missed paddle
            if ball_y >= height:
                lives -= 1
                ball_x, ball_y = width // 2, height - 3
                ball_dx, ball_dy = random.choice([-1, 1]), -1
                time.sleep(0.8)

        # --- End screen ---
        os.system("cls" if os.name == "nt" else "clear")
        if bricks_broken >= target_bricks_broken:
            print("\n✅ Lock destroyed! You broke through the cell!")
            time.sleep(1)
            return True
        else:
            print("\n💀 You ran out of drill bits...")
            time.sleep(1)
            return False

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def prison_hack_minigame():
    """Simple memory-based hack — remember a short code."""
    os.system("cls" if os.name == "nt" else "clear")
    print("💻 HACKING PRISON SYSTEM...")
    code = "".join(random.choice("#0987654321") for _ in range(5))
    print(f"Memorize this code: {code}")
    time.sleep(7)
    os.system("cls" if os.name == "nt" else "clear")

    guess = input("Enter the code: ").strip().upper()
    if guess == code:
        print("✅ Access granted.")
        return True
    else:
        print("❌ Wrong code!")
        return False


#heist minigams------------------------------------- End---------------


def heist_prison_break():
    """🚨 PRISON BREAK HEIST — 3-stage interactive mission requiring full gear."""
    global balance, heist_history, heist_wanted_flags, days_passed, heist_inventory

    print("\n=== 🏛️ PRISON BREAK HEIST ===")

    # --- Required gear ---
    required_items = [
        "Fake ID",
        "Spare Drill Bit",
        "Drill",
        "Hacking Software",
        "Hacking LapTop",
        "Guard uniform",
        "Get Away Car",
        "Inside Man Fee"
    ]

    # --- Check missing items ---
    missing_items = [item for item in required_items if item not in heist_inventory or heist_inventory[item] <= 0]
    if missing_items:
        print("🚫 You don’t have all the required gear for this heist!")
        print("Missing items:")
        for item in missing_items:
            print(f"  - {item}")
        print("\n💡 Buy missing gear from the Heist Equipment shop before trying again.")
        return

    # --- Show player what will be consumed ---
    print("\n⚠️ WARNING: Starting this heist will CONSUME the following items:")
    for item in required_items:
        print(f"  - {item}")
    print("Once the heist begins, all these items will be lost whether you succeed or fail.")

    # --- Ask for confirmation ---
    proceed = input("\nDo you still want to proceed with the Prison Break heist? (y/n): ").strip().lower()
    if proceed != "y":
        print("❌ Heist canceled. Your gear remains intact.")
        return

    # --- Deduct Inside Man Fee (cash requirement) ---
    inside_fee = 15000
    if balance < inside_fee:
        print(f"💰 You need at least {format_money(inside_fee)} for the Inside Man’s fee.")
        return
    balance -= inside_fee
    print(f"🕵️ Inside Man paid {format_money(inside_fee)} for inside access.")
    time.sleep(1)

    # --- Consume all items now (since player confirmed) ---
    for item in required_items:
        if item in heist_inventory:
            heist_inventory[item] -= 1
            if heist_inventory[item] <= 0:
                del heist_inventory[item]
    print("\n🧰 All required gear has been consumed for the heist.")
    time.sleep(1)

    print("\nStep 1️⃣  Hack into the prison’s main system...")
    time.sleep(1)

    # --- Step 1: Hack phase ---
    if not prison_hack_minigame():
        print("❌ You failed to breach the system! Authorities traced your signal.")
        total_p = 0.15
        days = HEIST_WANTED_DAYS if 'HEIST_WANTED_DAYS' in globals() else 60
        daily_p = 1 - (1 - total_p) ** (1.0 / days)
        heist_wanted_flags.append({
            "type": "Prison Break",
            "days_left": days,
            "daily_catch_p": daily_p,
            "total_catch": total_p,
            "created_day": days_passed
        })
        save_game()
        return

    print("\n✅ System breached. Inmate location found.")
    time.sleep(1.2)

    print("\nStep 2️⃣  Break the cell lock...")
    time.sleep(1)

    # --- Step 2: Breakout phase (2 attempts) ---
    for attempt in range(1, 3):
        print(f"\n🔧 Attempt {attempt} of 2 to break the lock!")
        success = breakout_lock_minigame()
        if success:
            print("\n✅ Lock broken successfully!")
            break
        elif attempt < 2:
            print("⚙️ The lock held tight... time for one more try!")
            time.sleep(1.5)
        else:
            print("💀 The alarm triggered during the breakout!")
            total_p = 0.20
            days = HEIST_WANTED_DAYS if 'HEIST_WANTED_DAYS' in globals() else 60
            daily_p = 1 - (1 - total_p) ** (1.0 / days)
            heist_wanted_flags.append({
                "type": "Prison Break",
                "days_left": days,
                "daily_catch_p": daily_p,
                "total_catch": total_p,
                "created_day": days_passed
            })
            print(f"⚠️ You are now wanted for {days} days (lock alarm triggered).")
            save_game()
            return

    # --- Step 3: Getaway phase ---
    print("\nStep 3️⃣  Make your getaway!")
    time.sleep(1)
    if not ascii_getaway_minigame():
        print("\n🚨 You managed to escape temporarily, but the authorities are searching for you!")
        total_p = 0.35
        days = HEIST_WANTED_DAYS if 'HEIST_WANTED_DAYS' in globals() else 60
        daily_p = 1 - (1 - total_p) ** (1.0 / days)
        heist_wanted_flags.append({
            "type": "Prison Break",
            "days_left": days,
            "daily_catch_p": daily_p,
            "total_catch": total_p,
            "created_day": days_passed
        })
        print(f"⚠️ You are now wanted for {days} days. Total capture chance over that period: {int(total_p*100)}%")
        save_game()
        time.sleep(2)
        return

    # --- Success! ---
    payout = random.randint(60000, 1200000)
    balance += payout
    print(f"\n💰 You successfully broke out the inmate and escaped with {format_money(payout)}!")
    print("Your reputation in the underworld has skyrocketed...")

    heist_history.append({
        "type": "Prison Break",
        "result": "Success",
        "day": days_passed,
        "gain": payout
    })

    # Add small wanted flag even on success (low residual heat)
    total_p = 0.35
    days = HEIST_WANTED_DAYS if 'HEIST_WANTED_DAYS' in globals() else 60
    daily_p = 1 - (1 - total_p) ** (1.0 / days)
    heist_wanted_flags.append({
        "type": "Prison Break",
        "days_left": days,
        "daily_catch_p": daily_p,
        "total_catch": total_p,
        "created_day": days_passed
    })

    save_game()
    time.sleep(2)


def start_bank_heist():
    """Attempt bank heist: requires gear, consumes items on attempt, one retry allowed.
    If player fails first attempt and retries, overall wanted risk is increased slightly.
    """
    global balance, bank_balance, heist_wanted_flags, heist_history, heist_inventory

    required = ["Fake ID", "Passport", "Credit Card (cloned)", "Drill", "Hacking Software","Inside Man Fee","Spare Drill Bit","Hacking LapTop"]
    missing = [r for r in required if heist_inventory.get(r, 0) <= 0]
    if missing:
        print("\nYou lack required equipment:", ", ".join(missing))
        print("Buy missing gear first.")
        return

    # Ask player to confirm consuming gear
    print("\nAttempting Bank Heist will consume one unit of each required item.")
    confirm = input("Proceed and use the equipment? (y/n): ").strip().lower()
    if confirm != "y":
        print("Heist aborted.")
        return

    # Consume required items (remove from inventory)
    for r in required:
        heist_inventory[r] = heist_inventory.get(r, 0) - 1
        if heist_inventory[r] <= 0:
            del heist_inventory[r]

    # Cost to run heist (operational fictional fee)
    upfront_cost = 5000
    if balance + bank_balance < upfront_cost:
        print("You need extra cash to fund operatives for the heist.")
        # refund equipment? we already consumed them per design — inform player
        print("Note: equipment was consumed. Buy new gear if you still want to try.")
        return
    # Deduct from cash first
    pay_from_cash = min(balance, upfront_cost)
    balance -= pay_from_cash
    rem = upfront_cost - pay_from_cash
    if rem > 0:
        bank_balance -= rem

    # Attempt sequence: hacking then drilling.
    # Allow one retry if first attempt fails (consumes no extra equipment)
    first_attempt_failed = False

    print("\nStarting Bank Heist — complete the hacking mini-game to disable alarms.")
    hack_ok = _play_hack_minigame()
    if not hack_ok:
        first_attempt_failed = True
        print("The hack failed on attempt #1.")
        retry = input("You have one more chance to retry the hack. Retry now? (y/n): ").strip().lower()
        if retry == "y":
            print("Retrying hacking mini-game...")
            hack_ok = _play_hack_minigame()
        else:
            print("Heist aborted after failed hack. You escaped but gain nothing.")
            heist_history.append({"type": "bank", "result": "Failed hack (no retry)", "day": days_passed, "gain": 0})
            save_game()
            return

    if not hack_ok:
        # failed both attempts
        print("Both hack attempts failed — abort and flee.")
        heist_history.append({"type": "bank", "result": "Failed hack (both attempts)", "day": days_passed, "gain": 0})
        save_game()
        # Slightly increase risk because alarms were triggered and escape was messy
        total_p = HEIST_CATCH_PROB_TOTAL + 0.05
        daily_p = 1 - (1 - total_p) ** (1.0 / HEIST_WANTED_DAYS)
        heist_wanted_flags.append({
            "type": "bank",
            "days_left": HEIST_WANTED_DAYS,
            "daily_catch_p": daily_p,
            "total_catch": total_p,
            "created_day": days_passed
        })
        print(f"⚠️ You're now at higher alert for {HEIST_WANTED_DAYS} days (total catch chance ~{int(total_p*100)}%).")
        return

    # Hacking succeeded — proceed to drilling
    print("\nHacking succeeded. Proceed to the drilling mini-game to open the vault.")
    drill_ok = _play_drill_minigame()
    if not drill_ok:
        first_attempt_failed = True
        print("Drill failed on attempt #1.")
        retry = input("You have one more chance to retry the drill. Retry now? (y/n): ").strip().lower()
        if retry == "y":
            print("Retrying drilling mini-game...")
            drill_ok = _play_drill_minigame()
        else:
            print("Heist aborted after failed drill. You escape but gain nothing.")
            heist_history.append({"type": "bank", "result": "Failed drill (no retry)", "day": days_passed, "gain": 0})
            save_game()
            return

    if not drill_ok:
        # failed both drill attempts
        print("Both drill attempts failed — abort and flee.")
        heist_history.append({"type": "bank", "result": "Failed drill (both attempts)", "day": days_passed, "gain": 0})
        save_game()
        # Slightly increase risk because alarms were triggered and escape was messy
        total_p = HEIST_CATCH_PROB_TOTAL + 0.05
        daily_p = 1 - (1 - total_p) ** (1.0 / HEIST_WANTED_DAYS)
        heist_wanted_flags.append({
            "type": "bank",
            "days_left": HEIST_WANTED_DAYS,
            "daily_catch_p": daily_p,
            "total_catch": total_p,
            "created_day": days_passed
        })
        print(f"⚠️ You're now at higher alert for {HEIST_WANTED_DAYS} days (total catch chance ~{int(total_p*100)}%).")
        return

    # If we reach here, both hack and drill succeeded (either on first or retry)
    reward = random.randint(45000, 1500000)
    balance += reward
    print(f"\n🏆 Bank Heist succeeded! You acquired {format_money(reward)} in cash.")
    heist_history.append({"type": "bank", "result": "Success", "day": days_passed, "gain": reward})

    # If first attempt failed at any stage but final succeeded, increase alert slightly
    total_p = HEIST_CATCH_PROB_TOTAL
    if first_attempt_failed:
        total_p = min(1.0, HEIST_CATCH_PROB_TOTAL + 0.05)  # slight increase on messy ops

    daily_p = 1 - (1 - total_p) ** (1.0 / HEIST_WANTED_DAYS)
    heist_wanted_flags.append({
        "type": "bank",
        "days_left": HEIST_WANTED_DAYS,
        "daily_catch_p": daily_p,
        "total_catch": total_p,
        "created_day": days_passed
    })
    print(f"⚠️ You are now wanted for the next {HEIST_WANTED_DAYS} days. There is a {int(total_p*100)}% chance you'll be caught during that period.")
    save_game()

def start_hacking_heist():
    """Attempt hacking heist: consumes required items, one retry allowed, slight risk increase on first-fail."""
    global balance, bank_balance, heist_history, heist_wanted_flags, heist_inventory

    required = ["Hacking Software", "Inside Man Fee","Hacking LapTop","Credit Card (cloned)"]
    missing = [r for r in required if heist_inventory.get(r, 0) <= 0]
    if missing:
        print("\nYou lack required equipment:", ", ".join(missing))
        print("Buy missing gear first.")
        return

    # Confirm consumption of gear
    print("\nAttempting Hacking Heist will consume one unit of each required item.")
    confirm = input("Proceed and use the equipment? (y/n): ").strip().lower()
    if confirm != "y":
        print("Heist aborted.")
        return

    # Consume required items (remove from inventory)
    for r in required:
        heist_inventory[r] = heist_inventory.get(r, 0) - 1
        if heist_inventory[r] <= 0:
            del heist_inventory[r]

    # Fund the operation (small upfront)
    upfront_cost = 3000
    if balance + bank_balance < upfront_cost:
        print("You need extra funds for the hacking crew.")
        print("Note: equipment was consumed. Buy new gear if you still want to try.")
        return
    pay_from_cash = min(balance, upfront_cost)
    balance -= pay_from_cash
    rem = upfront_cost - pay_from_cash
    if rem > 0:
        bank_balance -= rem

    first_attempt_failed = False

    print("\nStarting Hacking Heist — infiltrate target's portfolio.")
    infil_ok = _play_portfolio_hack_minigame()
    if not infil_ok:
        first_attempt_failed = True
        print("Infiltration failed on attempt #1.")
        retry = input("You have one more chance to retry infiltration. Retry now? (y/n): ").strip().lower()
        if retry == "y":
            infil_ok = _play_portfolio_hack_minigame()
        else:
            print("Operation aborted after failed infiltration.")
            heist_history.append({"type": "hacking", "result": "Failed infiltration (no retry)", "day": days_passed, "gain": 0})
            save_game()
            return

    if not infil_ok:
        print("Both infiltration attempts failed.")
        heist_history.append({"type": "hacking", "result": "Failed infiltration (both attempts)", "day": days_passed, "gain": 0})
        save_game()
        total_p = HEIST_CATCH_PROB_TOTAL + 0.05
        daily_p = 1 - (1 - total_p) ** (1.0 / HEIST_WANTED_DAYS)
        heist_wanted_flags.append({
            "type": "hacking",
            "days_left": HEIST_WANTED_DAYS,
            "daily_catch_p": daily_p,
            "total_catch": total_p,
            "created_day": days_passed
        })
        print(f"⚠️ You are now at higher alert for {HEIST_WANTED_DAYS} days (total catch chance ~{int(total_p*100)}%).")
        return

    # Extraction phase
    steal_ok, mult = _play_steal_money_minigame()
    if not steal_ok:
        first_attempt_failed = True
        print("Extraction failed on attempt #1.")
        retry = input("You have one more chance to retry extraction. Retry now? (y/n): ").strip().lower()
        if retry == "y":
            steal_ok, mult = _play_steal_money_minigame()
        else:
            print("Extraction aborted after failed attempt.")
            heist_history.append({"type": "hacking", "result": "Failed extraction (no retry)", "day": days_passed, "gain": 0})
            save_game()
            return

    if not steal_ok:
        print("Both extraction attempts failed.")
        heist_history.append({"type": "hacking", "result": "Failed extraction (both attempts)", "day": days_passed, "gain": 0})
        save_game()
        total_p = HEIST_CATCH_PROB_TOTAL + 0.05
        daily_p = 1 - (1 - total_p) ** (1.0 / HEIST_WANTED_DAYS)
        heist_wanted_flags.append({
            "type": "hacking",
            "days_left": HEIST_WANTED_DAYS,
            "daily_catch_p": daily_p,
            "total_catch": total_p,
            "created_day": days_passed
        })
        print(f"⚠️ You are now at higher alert for {HEIST_WANTED_DAYS} days (total catch chance ~{int(total_p*100)}%).")
        return

    # Success
    base = random.randint(25000, 60000)
    gain = int(base * mult)
    balance += gain
    print(f"\n🏆 Hacking Heist succeeded! You netted {format_money(gain)}.")
    heist_history.append({"type": "hacking", "result": "Success", "day": days_passed, "gain": gain})

    total_p = HEIST_CATCH_PROB_TOTAL
    if first_attempt_failed:
        total_p = min(1.0, HEIST_CATCH_PROB_TOTAL + 0.05)

    daily_p = 1 - (1 - total_p) ** (1.0 / HEIST_WANTED_DAYS)
    heist_wanted_flags.append({
        "type": "hacking",
        "days_left": HEIST_WANTED_DAYS,
        "daily_catch_p": daily_p,
        "total_catch": total_p,
        "created_day": days_passed
    })
    print(f"⚠️ You are now wanted for the next {HEIST_WANTED_DAYS} days. There is a {int(total_p*100)}% chance you'll be caught during that period.")
    save_game()

def process_heist_wanted():
    """Called each new in-game day: decrement wanted flags and roll for capture.

    If caught:
      - Seize bank balance
      - Confiscate Fake ID and lock new purchases for FAKE_ID_LOCK_DAYS
      - Reset bank interest rate to 0
      - Lose all portfolio stocks
      - Set cash to $1500
    """
    global heist_wanted_flags, bank_balance, balance, heist_history
    global player_has_fake_id, FAKE_ID_COST, fake_id_locked_until, days_passed, bank_interest_rate
    global portfolio

    if not heist_wanted_flags:
        return

    for flag in list(heist_wanted_flags):
        # Each day sample the daily catch probability
        if random.random() < flag.get("daily_catch_p", 0):
            # caught!
            print(f"\n🚨 You have been caught for a {flag['type']} heist! Authorities have seized your assets.")

            # Lose all bank money
            bank_balance = 0.0

            # Lose all stocks/portfolio
            portfolio.clear()
            print("📉 All your stock holdings have been liquidated by authorities.")

            # Reset cash to $1500
            balance = 1500.0
            print("💸 Your cash on hand has been reset to $1,500.")

            # confiscate Fake ID and lock purchases for FAKE_ID_LOCK_DAYS
            if player_has_fake_id:
                player_has_fake_id = False
                try:
                    FAKE_ID_COST = round(FAKE_ID_COST * 1.15, 2)
                except Exception:
                    FAKE_ID_COST = round(FAKE_ID_COST * 1.15, 2)
                fake_id_locked_until = days_passed + FAKE_ID_LOCK_DAYS
                print(f"🪪 Your Fake ID was confiscated. You cannot buy a new one for {FAKE_ID_LOCK_DAYS} in-game days.")
                print(f"Next available Fake ID purchase after day {fake_id_locked_until}.")

            # reset bank interest to 0
            bank_interest_rate = 0.0
            print("🏦 Your bank interest rate has been reset to 0 due to capture.")

            # record event
            heist_history.append({
                "type": flag["type"],
                "result": "Caught",
                "day": days_passed,
                "gain": 0
            })

            heist_wanted_flags.remove(flag)
            save_game()
            return
        else:
            flag["days_left"] -= 1
            if flag["days_left"] <= 0:
                heist_history.append({
                    "type": flag["type"],
                    "result": "Period expired - not caught",
                    "day": days_passed,
                    "gain": 0
                })
                heist_wanted_flags.remove(flag)

    save_game()


def view_heist_status():
    """Display current wanted flags / heist cooldowns."""
    global heist_wanted_flags

    print("\n=== 🚔 Heist Status / Wanted Flags ===")
    if not heist_wanted_flags:
        print("✅ No active wanted levels or heist cooldowns.")
        return

    for f in heist_wanted_flags:
        heist_type = f.get("type", "Unknown")
        days_left = f.get("days_left", 0)
        total_catch = f.get("total_catch", 0.0)  # ✅ Default if missing

        print(f"Type: {heist_type:<8} | Days left: {days_left:>3} | Total catch chance: {int(total_catch * 100)}%")

    print("\nHeist cooldowns reset over time — stay under the radar to lower catch chances.")



#END OF HEIST------------------------------------------------

#----Insider Info
def buy_insider_info():
    global balance, INSIDER_INFO_COST, insider_predictions, days_passed, stocks
    print(f"Current cost for insider info: ${INSIDER_INFO_COST:,.2f}")
    confirm = input("Buy insider info for a random stock? (y/n): ").strip().lower()
    if confirm != "y":
        return

    if balance < INSIDER_INFO_COST:
        print("You don't have enough money.")
        return

    balance -= INSIDER_INFO_COST
    stock_name = random.choice(list(stocks.keys()))
    direction = random.choice(["up", "down"])
    accuracy_chance = 0.65
    accurate = random.random() < accuracy_chance

    predicted = direction if accurate else ("up" if direction == "down" else "down")

    insider_predictions[stock_name] = {
        "predicted_direction": predicted,
        "trend": predicted,      # compatibility with older references
        "accuracy": accuracy_chance,  # ✅ now included
        "days_left": 10
    }

    print(
        f"📊 Insider info acquired on {stock_name} — expected to go "
        f"{predicted.upper()} for the next 10 days (accuracy {accuracy_chance*100:.0f}%)."
    )
    INSIDER_INFO_COST = int(INSIDER_INFO_COST * 1.15)
    save_game()

# ==============================
# 💰 CRYPTOCURRENCY SYSTEM
# ==============================

cryptos = {}             # name -> current price
crypto_portfolio = {}    # name -> {"qty": float, "avg_price": float}
crypto_supply = {}       # name -> total supply
crypto_history = {}      # name -> list of past prices

CRYPTO_CREATION_COST = 150000.0
CRYPTO_CREATOR_OWNERSHIP = 0.65
BUY_IMPACT_FACTOR = 1.2    # price rises up to 1.2% per 1% of supply bought
SELL_IMPACT_FACTOR = 1.5   # price falls up to 1.5% per 1% of supply sold


def crypto_menu():
    """Main Crypto Menu for creating and managing your coins."""
    global balance
    while True:
        print("\n=== 🪙 CRYPTO MENU ===")
        show_crypto_market()
        show_crypto_portfolio()
        print("\n[C] Create New Cryptocurrency ($150,000) | [S] Sell Cryptocurrency | [B] Buy Cryptocurrency ")
        print("[D] Dump All of a Cryptocurrency | [G] View 60-Day Crypto Graph 📈 | [Q]Return to Main Menu")
      #  print("V) View Crypto Market")
        choice = input("Choose option: ").strip().lower()

        if choice == "c":
            create_crypto()
        elif choice == "s":
            sell_crypto()
        elif choice == "3":
            dump_crypto()
        elif choice == "0":
            show_crypto_market()
        elif choice == "g":
            crypto_name = input("Enter crypto name to view graph: ").upper().strip()
            show_crypto_graph(crypto_name)
        elif choice == "b":
            buy_crypto()
        elif choice == "q":
            print("Returning to main menu...")
            break
        else:
            print("Invalid choice.")


def create_crypto():
    """Let player create a new cryptocurrency and own 65% of supply."""
    global balance

    if balance < CRYPTO_CREATION_COST:
        print(f"❌ You need at least ${CRYPTO_CREATION_COST:,.2f} to create a cryptocurrency.")
        return

    name = input("Enter your new cryptocurrency name (e.g., BUSCOIN): ").upper().strip()
    if not name or name in cryptos:
        print("❌ Invalid or duplicate name.")
        return

    try:
        supply = int(input("Enter total supply (1 - 100,000,000): "))
        if supply < 1 or supply > 100_000_000:
            print("❌ Supply must be between 1 and 100,000,000.")
            return
    except ValueError:
        print("❌ Invalid supply number.")
        return

    balance -= CRYPTO_CREATION_COST
    start_price = 0.0010
    cryptos[name] = start_price
    crypto_supply[name] = supply
    crypto_history[name] = [start_price]

    owned_qty = int(supply * CRYPTO_CREATOR_OWNERSHIP)
    crypto_portfolio[name] = {"qty": owned_qty, "avg_price": start_price}

    print(f"✅ Created {name} with total supply {supply:,}.")
    print(f"💵 Starting price: ${start_price:.4f}")
    print(f"🏦 You automatically own {owned_qty:,} units ({CRYPTO_CREATOR_OWNERSHIP*100:.0f}% of total supply).")


def update_cryptos():
    """Simulate daily price movement for cryptocurrencies."""
    global cryptos, crypto_history
    if not cryptos:
        return

    for name, price in list(cryptos.items()):
        if price <= 0:
            price = random.uniform(0.01, 0.10)

        drift = -0.002
        volatility = 0.18
        Z = np.random.normal(0, 1)
        new_price = price * math.exp((drift - 0.5 * volatility ** 2) + volatility * Z)

        roll = random.random()
        if roll < 0.02:
            new_price *= random.uniform(0.1, 0.5)
        elif roll > 0.98:
            new_price *= random.uniform(1.5, 3.0)

        new_price = max(0.0001, min(new_price, 10_000_000))
        new_price = round(new_price, 4)
        cryptos[name] = new_price
        crypto_history.setdefault(name, []).append(new_price)


def show_crypto_market():
    """Display all player-created cryptos with performance."""
    if not cryptos:
        print("\nNo cryptocurrencies exist yet.")
        return

    print("\n=== 📊 CRYPTO MARKET ===")
    print("Name       | Price ($) | Supply     | 30d Change")
    print("-------------------------------------------------")
    for name, price in cryptos.items():
        hist = crypto_history.get(name, [price])
        old_price = hist[-30] if len(hist) >= 30 else hist[0]
        change = ((price - old_price) / old_price * 100) if old_price > 0 else 0
        arrow = "📈" if change > 0 else ("📉" if change < 0 else "➖")
        color = "\033[92m" if change > 0 else ("\033[91m" if change < 0 else "\033[0m")
        print(f"{name:<10} | ${price:<8.4f} | {crypto_supply[name]:<10,} | {color}{arrow} {change:+.2f}%\033[0m")
    print("-------------------------------------------------")


def show_crypto_portfolio():
    """Display the player's crypto holdings with live Gain/Loss updates."""
    total_value = balance
    total_gain_loss_value = 0.0

    print("\n=== 💼 CRYPTO PORTFOLIO ===")
    if not crypto_portfolio:
        print("You don't own any cryptocurrency yet.")
        print(f"💰 Cash: {format_money(balance)}")
        return

    for name, data in crypto_portfolio.items():
        qty = data["qty"]
        avg_price = data["avg_price"]
        current_price = cryptos.get(name, 0.0010)

        value = qty * current_price
        cost_basis = qty * avg_price
        gain_value = value - cost_basis
        gain_percent = (gain_value / cost_basis * 100) if cost_basis > 0 else 0.0

        total_value += value
        total_gain_loss_value += gain_value

        arrow = "📈" if gain_value > 0 else ("📉" if gain_value < 0 else "➖")
        color = "\033[92m" if gain_value > 0 else ("\033[91m" if gain_value < 0 else "\033[0m")

        print(
            f"{name}: {qty:,.0f} units | "
            f"Price: ${current_price:.4f} | "
            f"Value: {format_money(value)} | "
           # f"Cost: {format_money(cost_basis)} | "
            f"{color}{arrow} G/L: {gain_percent:+.2f}% ({format_money(gain_value)})\033[0m"
        )

    print("-------------------------------------------------")
    print(f"💰 Cash: {format_money(balance)}")
    print(f"📊 Portfolio Total Value (excl. cash): {format_money(total_value - balance)}")
    print(f"📈 Net Worth (inc. cash): {format_money(total_value)}")
    print(f"🧮 Total Gain/Loss: {format_money(total_gain_loss_value)}")


def buy_crypto():
    """Allow the player to buy more of their existing cryptocurrencies with price impact."""
    global balance

    if not cryptos:
        print("❌ No cryptocurrencies available to buy.")
        return

    show_crypto_market()
    name = input("Enter crypto name to buy: ").upper().strip()
    if name not in cryptos:
        print("❌ Invalid crypto name.")
        return

    current_price = cryptos[name]
    total_supply = crypto_supply[name]
    print(f"{name} is currently trading at ${current_price:.4f} per unit.")
    try:
        qty = float(input("Enter amount to buy: "))
        if qty <= 0:
            print("❌ Invalid quantity.")
            return
    except ValueError:
        print("❌ Invalid input.")
        return

    cost = qty * current_price
    if balance < cost:
        print(f"❌ You don't have enough money. You need {format_money(cost)}, but only have {format_money(balance)}.")
        return

    # Price impact based on supply
    impact_ratio = qty / total_supply
    new_price = current_price * (1 + impact_ratio * BUY_IMPACT_FACTOR)
    cryptos[name] = round(new_price, 4)
    crypto_history[name].append(new_price)

    balance -= cost

    if name in crypto_portfolio:
        old_data = crypto_portfolio[name]
        old_qty = old_data["qty"]
        old_avg = old_data["avg_price"]
        new_total_qty = old_qty + qty
        new_avg_price = ((old_avg * old_qty) + (current_price * qty)) / new_total_qty
        crypto_portfolio[name] = {"qty": new_total_qty, "avg_price": new_avg_price}
    else:
        crypto_portfolio[name] = {"qty": qty, "avg_price": current_price}

    print(f"✅ Bought {qty:,.0f} {name} for {format_money(cost)} at ${current_price:.4f} each.")
    print(f"📈 {name} price increased to ${new_price:.4f} due to market demand!")
    update_cryptos()


def sell_crypto():
    """Sell part of your holdings with price impact."""
    global balance
    if not crypto_portfolio:
        print("You don't own any crypto.")
        return

    name = input("Enter crypto name to sell: ").upper()
    if name not in crypto_portfolio:
        print("You don't own that crypto.")
        return

    try:
        qty = float(input("Enter amount to sell: "))
    except ValueError:
        print("Invalid number.")
        return

    if qty <= 0 or qty > crypto_portfolio[name]["qty"]:
        print("Invalid quantity.")
        return

    current_price = cryptos.get(name, 0)
    total_supply = crypto_supply[name]
    proceeds = qty * current_price
    balance += proceeds
    crypto_portfolio[name]["qty"] -= qty
    if crypto_portfolio[name]["qty"] <= 0:
        del crypto_portfolio[name]

    # Price impact from selling
    impact_ratio = qty / total_supply
    new_price = current_price * (1 - impact_ratio * SELL_IMPACT_FACTOR)
    new_price = max(0.0001, new_price)
    cryptos[name] = round(new_price, 4)
    crypto_history[name].append(new_price)

    print(f"✅ Sold {qty:,.0f} {name} for {format_money(proceeds)}.")
    print(f"📉 {name} price dropped to ${new_price:.4f} due to market selling pressure!")
    update_cryptos()


def dump_crypto():
    """Sell ALL of one crypto at once."""
    global balance
    if not crypto_portfolio:
        print("You don't own any crypto.")
        return

    name = input("Enter crypto name to dump: ").upper()
    if name not in crypto_portfolio:
        print("You don't own that crypto.")
        return

    qty = crypto_portfolio[name]["qty"]
    price = cryptos.get(name, 0)
    proceeds = qty * price
    balance += proceeds
    del crypto_portfolio[name]

    # Apply full price crash for dumping entire position
    new_price = max(0.0001, price * 0.5)
    cryptos[name] = round(new_price, 4)
    crypto_history[name].append(new_price)

    print(f"💥 Dumped ALL {qty:,.0f} {name} for {format_money(proceeds)}!")
    print(f"📉 {name} price crashed to ${new_price:.4f} due to the massive sell-off!")


def show_crypto_graph(name):
    """Show 60-day candlestick-style chart for a given cryptocurrency."""
    if name not in crypto_history or len(crypto_history[name]) < 2:
        print("❌ No history for that crypto yet.")
        return

    data = crypto_history[name][-60:]
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=len(data) - 1)

    ohlc = []
    for i, close_price in enumerate(data):
        date = start_date + datetime.timedelta(days=i)
        date_num = mdates.date2num(date)
        open_price = data[i - 1] if i > 0 else close_price
        wiggle = random.uniform(0.002, 0.04)
        high = max(open_price, close_price) * (1 + random.uniform(0.0, wiggle))
        low = min(open_price, close_price) * (1 - random.uniform(0.0, wiggle))
        if low <= 0:
            low = 0.0001
        ohlc.append([date_num, open_price, high, low, close_price])

    fig, ax = plt.subplots(figsize=(10, 5))
    width = 0.6
    for date_num, open_p, high, low, close_p in ohlc:
        color = "green" if close_p >= open_p else "red"
        ax.plot([date_num, date_num], [low, high], color="black", linewidth=1)
        lower = min(open_p, close_p)
        height = abs(close_p - open_p)
        if height == 0:
            height = (high - low) * 0.001
        rect = Rectangle((date_num - width / 2, lower), width, height, facecolor=color, edgecolor="black", alpha=0.85)
        ax.add_patch(rect)

    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.set_title(f"{name} Price History (Last {len(data)} Days) - Crypto Chart")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price ($)")
    plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment="right")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    
#SEARCH---------------
import threading

def search_stock():
    """Search for a stock by name and highlight it on the available stocks page."""
    global stocks

    query = input("🔍 Enter stock name to search: ").strip().upper()
    if not query:
        print("Search canceled.")
        return

    # Find matching stocks (case-insensitive, supports partials)
    matching = [name for name in stocks.keys() if query in name.upper()]
    if not matching:
        print("❌ No stocks found matching your search.")
        return

    # Pick first match (or prompt if you want to support multiple)
    stock_name = matching[0]

    # Find which page it's on
    per_page = 10
    stock_names = list(stocks.keys())
    stock_index = stock_names.index(stock_name)
    page = stock_index // per_page

    # Show that page with highlight
    highlight_stock(stock_name, page)
def highlight_stock(stock_name, page):
    """Show the page containing the searched stock with temporary green highlight."""
    global stocks, portfolio

    GREEN = "\033[92m"
    RESET = "\033[0m"

    stock_names = list(stocks.keys())
    per_page = 10
    start = page * per_page
    end = start + per_page
    visible_stocks = stock_names[start:end]

    print("\n📈 Available Stocks (Search Result Highlighted)")
    print("════════════════════════════════════════════════════════")
    print(f"{'Name':<15}{'Price':<12}")
    print("────────────────────────────────────────────────────────")

    for name in visible_stocks:
        price = stocks[name]
        change = get_stock_change(name) if 'get_stock_change' in globals() else 0.0
        change_str = f"{change:+.2f}%"
        color = "\033[92m" if change >= 0 else "\033[91m"
        reset = "\033[0m"

        # Ownership %
        shares_owned = portfolio.get(name, {}).get("shares", 0)
        total_shares = 1000
        ownership_pct = min((shares_owned / total_shares) * 100, 100)
        owned_icon = "✅" if ownership_pct >= 100 else ""
        ownership_display = f"{ownership_pct:>6.2f}% {owned_icon}"

        # Highlight searched stock
        if name == stock_name:
            print(f"{GREEN}{name:<15}${price:<10.2f}{color}{RESET}")
        else:
            print(f"{name:<15}${price:<10.2f}{color}{reset}")

    print("════════════════════════════════════════════════════════")
    print(f"Page {page + 1} of {((len(stock_names) - 1) // per_page) + 1}")

    # Automatically remove highlight after 10 seconds
    threading.Timer(10.0, lambda: print_stocks(page)).start()
    
    
#admin menu-------------------------------------
def admin_menu():
    """Hidden admin tools for debugging and testing."""
    global balance, bank_balance, days_passed, portfolio, stocks, heist_wanted_flags

    print("\n🔒 Enter admin password:")
    password = input("> ").strip()
    if password != "sus":
        print("❌ Incorrect password.")
        return

    print("\n✅ Access granted. Welcome, Admin.")

    while True:
        print("\n=== 🧰 ADMIN MENU ===")
        print("1) Add Money")
        print("2) Fast Forward Time (Free)")
        print("3) Add Stocks to Portfolio")
        print("4) Change Stock Prices")
        print("HEIST Mini-Games)")
        print("- Drill (D_G), Money Grab (M_G), Number Guessing (#_G), Hacking (H_G)")
        print("- Get way game (C_G), Breakout lock game (L_G), Prison Hack game (H2_G)")
        print("Q) Exit Admin Menu")

        choice = input("\nChoose an option: ").strip()

        # --- 1) Add Money ---
        if choice == "1":
            try:
                amt = float(input("Enter amount to add: "))
                target = input("Add to (cash/bank)? ").strip().lower()
                if target == "cash":
                    balance += amt
                elif target == "bank":
                    bank_balance += amt
                else:
                    print("Invalid target.")
                    continue
                print(f"💰 Added ${amt:,.2f} to {target}.")
            except ValueError:
                print("Invalid amount.")

        # --- 2) Fast Forward ---
        elif choice == "2":
            try:
                days = int(input("Enter number of days to fast forward: "))
                for _ in range(days):
                    days_passed += 1
                    if 'apply_bank_interest' in globals():
                        if days_passed % 7 == 0:
                            apply_bank_interest()
                    if 'process_black_market_orders_daily' in globals():
                        process_black_market_orders_daily()
                    if 'heist_wanted_flags' in globals():
                        for flag in heist_wanted_flags[:]:
                            flag["days_left"] -= 1
                            if flag["days_left"] <= 0:
                                heist_wanted_flags.remove(flag)
                print(f"⏩ Fast-forwarded {days} days successfully.")
            except ValueError:
                print("Invalid input.")
                
        # --- 3) Add Stocks ---
        elif choice == "3":
            print("\nAvailable stocks:")

            # handle stocks whether dict or list
            stock_list = []
            if isinstance(stocks, dict):
                for name, data in stocks.items():
                    price = data["price"] if isinstance(data, dict) and "price" in data else data
                    stock_list.append((name, price))
            elif isinstance(stocks, list):
                for s in stocks:
                    if isinstance(s, dict):
                        stock_list.append((s.get("name", "Unknown"), s.get("price", 0.0)))
                    elif isinstance(s, str):
                        stock_list.append((s, 0.0))

            for i, (name, price) in enumerate(stock_list):
                print(f"{i+1}) {name} (${price:,.2f})")

            try:
                pick = int(input("Select stock number: ")) - 1
                qty = int(input("How many shares to add? "))
                if 0 <= pick < len(stock_list):
                    name = stock_list[pick][0]

                    # ✅ Maintain proper portfolio structure
                    if name in portfolio:
                        if isinstance(portfolio[name], dict):
                            portfolio[name]["qty"] += qty
                        else:
                            # Convert legacy integer entry
                            portfolio[name] = {
                                "qty": portfolio[name] + qty,
                                "avg_price": (
                                    stocks[name]["price"]
                                    if isinstance(stocks, dict)
                                    and name in stocks
                                    and isinstance(stocks[name], dict)
                                    and "price" in stocks[name]
                                    else 0.0
                                ),
                            }
                    else:
                        portfolio[name] = {
                            "qty": qty,
                            "avg_price": (
                                stocks[name]["price"]
                                if isinstance(stocks, dict)
                                and name in stocks
                                and isinstance(stocks[name], dict)
                                and "price" in stocks[name]
                                else 0.0
                            ),
                        }

                    print(f"📈 Added {qty} shares of {name} to portfolio.")
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Invalid input.")

 
        # --- 4) Change Stock Prices ---
        elif choice == "4":
            print("\nCurrent stock prices:")

            stock_list = []
            if isinstance(stocks, dict):
                for name, data in stocks.items():
                    price = data["price"] if isinstance(data, dict) and "price" in data else data
                    stock_list.append((name, price))
            elif isinstance(stocks, list):
                for s in stocks:
                    if isinstance(s, dict):
                        stock_list.append((s.get("name", "Unknown"), s.get("price", 0.0)))
                    elif isinstance(s, str):
                        stock_list.append((s, 0.0))

            for i, (name, price) in enumerate(stock_list):
                print(f"{i+1}) {name} (${price:,.2f})")

            try:
                pick = int(input("Select stock number: ")) - 1
                new_price = float(input("Enter new stock price: "))
                if 0 <= pick < len(stock_list):
                    stock_name = stock_list[pick][0]

                    # Update depending on structure
                    if isinstance(stocks, dict):
                        if isinstance(stocks[stock_name], dict):
                            stocks[stock_name]["price"] = new_price
                        else:
                            stocks[stock_name] = new_price
                    elif isinstance(stocks, list):
                        for s in stocks:
                            if isinstance(s, dict) and s.get("name") == stock_name:
                                s["price"] = new_price
                    print(f"💹 Changed {stock_name} price → ${new_price:,.2f}")
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Invalid input.")

        elif choice == "d_g":  _play_drill_minigame()
        elif choice == "m_g": _play_steal_money_minigame() 
        elif choice == "#_g": _play_portfolio_hack_minigame()
        elif choice == "h_g": _play_hack_minigame()
        elif choice == "c_g": ascii_getaway_minigame()
        elif choice == "l_g": breakout_lock_minigame()
        elif choice == "h2_g": prison_hack_minigame()
        


        # --- 5) Exit ---
        elif choice == "q":
            print("Exiting admin mode...")
            return

        else:
            print("Invalid choice.")

#end of admin menu-------------------------------------

def auto_save_if_needed():
    """Automatically save every few in-game days or major actions."""
    try:
        save_game()
    except Exception:
        pass

# --- Main ---
def main():
    global current_page, play_mode
    print("Welcome to Terminal Stock Simulator! Created by Mr.SusBus And AI")
    print("\nVer: 1.0.5")
    if not os.path.exists(SAVE_FILE):
        # No save: ensure stocks exist then choose mode
        choose_game_mode()
    else:
        if input("Load save? (y/n): ").lower() == "y":
            load_game()
        else:
            # if user opts not to load, offer fresh mode choose
            choose_game_mode()

    while True:
        if not play_mode:
            print_stocks(current_page)
            print_portfolio()
        print("\n[B] Buy | [S] Sell | [Sh] Short | [C] Cover | [Show All] [SEARCH] | [F] Fast Forward | [G] Graph | [H] History ")
        print("[Bank] | [DLC] | [Vegas] | [Play] | [N] Next | [P] Prev | [Save] | [Q] Quit | [NEW GAME] | [CMDS] list all CMDs")
        ch = input("Choose: ").lower().strip()
        if ch == "b": buy_stock()
        elif ch == "s": sell_stock()
        elif ch == "sell all":
            print("Are your Sure y/n")
            if a == "y": sell_all()
            elif a == "n":
                print_stocks(current_page)
                print_portfolio()
        elif ch == "sh": short_stock()
        elif ch == "new game": new_game()
        elif ch == "black market": black_market_menu()
        elif ch == "c": cover_short()
        elif ch == "crypto": crypto_menu()
        elif ch == "insider": buy_insider_info()
        elif ch == "admin": admin_menu()
        elif ch == "new stocks": show_all()  # left as-is
        elif ch == "show all": show_all()
        #elif ch == "drill game": _play_drill_minigame()
        elif ch == "search": search_stock()
        elif ch == "dlc": buy_dlc() if 'buy_dlc' in globals() else print("No DLC function available.")
        elif ch == "f":
            try:
                d = int(input("Days to fast forward: "))
            except:
                d = 5
            fast_forward(d)
        elif ch == "g":
            choice = input("Enter stock symbol OR type 'market' to graph the market: ").strip().lower()
            if not choice:
                continue
            if choice == "market":
                show_market_graph()
            else:
                show_graph(choice.upper())
        elif ch == "h": show_trade_history()
        elif ch == "bank":
            print(f"Cash: ${balance:.2f} | Bank: ${bank_balance:.2f}")
            print(f"Interest: {bank_interest_rate*100:.3f}% | Upgrade cost: ${bank_interest_cost:.2f}")
            a = input("(D)eposit, (W)ithdraw, (U)pgrade Interest, (CD) Certified Deposit Menu: ").lower()
            if a == "d": deposit_bank()
            elif a == "w": withdraw_bank()
            elif a == "u": buy_interest_upgrade()
            elif a == "cd": bank_cd_menu()
        elif ch == "play":
            play_mode = not play_mode
            if play_mode:
                threading.Thread(target=auto_play, daemon=True).start()
                print("▶ Auto-play started (updates every 15s).")
            else:
                print("⏸ Auto-play stopped.")
        elif ch == "n":
            if current_page < (len(stocks)//STOCKS_PER_PAGE): current_page += 1
        elif ch == "p":
            if current_page > 0: current_page -= 1
        elif ch == "save": save_game()
        elif ch == "q":
            save_game()
            print("Exiting...")
            break
        elif ch == "vegas":
            vegas_menu()
        elif ch == "cmds": 
            print("======Command List======")
            print("\nStocks:")
            print("B) buy stocks, S) sell stocks, SH) short stocks, C) cover stocks, G) show graph for stock")
            print("DLC) show stock DLCs, PLAY) go through time, F) Fast- forward through time, H) trade and purchase history")
            print("SAVE) save progress, Q) quit again and save, N) next page of stocks, P) previous page of stocks")
            print("SEARCH) look up stock to show what page it is on, NEW GAME) start a new game")
            print("\nBank:")
            print("BANK) bank menu, CD) Certified Deposit menu, D) deposit money, W) withdraw money, U) upgrade bank interest")
            print("\nExtra:")
            print("INSIDER) get insider info on a stock, BLACK MARKET) black market menu, CRYPTO) cryptocurrency menu")
            print("UPDATES) show update log, ADMIN) admin menu - password [sus] ")
        elif ch == "updates": 
            print("======Update Change Long======")
            print("\nUpated 1.0.2")
            print("\nAdded:")
            print("- Certified Deposit (CD) to the bank. CDs get 4-9% interest for 90-120 days $10k - $100k per, 200 day cool down,")
            print("you have 30 days to claim your CDs ater ther time period expires or else you will lose the money")
            print("\n- Update change log use command updates")
            print("\n- added 3 more rows to Slots and a Jackpot, the jackpot will go up with every bet you make and every day")
            print("\nFixed:")
            print("- Save and load game data points, CD cool down not reseting after new game")
            print("\nChanges:")
            print("- Fast-forward cost from $100 - $500 per day, CD interest from 2-9% to 0.2-0.9%, trade history to show last 20 to 100 trades")
            print("\nRoad Map: Off shore accounts, crypto curncey, improved heist games, more DLC, more black market items, more heist, improved black market menus, windows build, mobile game... ")
            print("\nUpated 1.0.5")
            print("\nAdded:")
            print("Cryptocurrency menuv[crypto], command list [cmds]")
        else:
            print("Invalid option.")
        

if __name__ == "__main__":
    main()
