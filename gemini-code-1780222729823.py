import requests
import os
import pytz
from datetime import datetime

# ============================================
# SETTINGS
# ============================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID   = os.environ.get("CHAT_ID", "")

# કેટલા ટકા (%) નો ફેરફાર થાય તો એલર્ટ જોઈએ છે? (0.5 એટલે અડધો ટકો)
THRESHOLD_PERCENT = 0.5  

IST = pytz.timezone("Asia/Kolkata")

def now_ist():
    return datetime.now(IST)

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        print("Telegram Response:", r.json().get("ok"))
    except Exception as e:
        print(f"Telegram error: {e}")

def fetch_bitcoin_data():
    # Binance API પરથી છેલ્લા ૨૪ કલાકનો અને કરંટ ડેટા લેવા માટે
    url = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
    try:
        r = requests.get(url, timeout=15)
        res = r.json()
        current_price = round(float(res["lastPrice"]), 2)
        price_change_percent = round(float(res["priceChangePercent"]), 2)
        high_price = round(float(res["highPrice"]), 2)
        low_price = round(float(res["lowPrice"]), 2)
        return current_price, price_change_percent, high_price, low_price
    except Exception as e:
        print(f"Fetch error: {e}")
        return None, None, None, None

price, change_pct, high, low = fetch_bitcoin_data()

if price is None:
    print("ડેટા મળી શક્યો નથી. સ્કીપ કરાય છે.")
    exit(0)

print(f"Bitcoin Price: ${price:,} | 24h Change: {change_pct}%")

# જો ૨૪ કલાકનો ફેરફાર આપણા સેટ કરેલા ટકા કરતાં વધારે (ઉપર કે નીચે) હોય તો એલર્ટ જશે
if abs(change_pct) >= THRESHOLD_PERCENT:
    if change_pct > 0:
        emoji = "🚀🟢 <b>BITCOIN BULLETS UP!</b>"
    else:
        emoji = "🚨🔴 <b>BITCOIN CRASHING!</b>"
        
    msg = f"""{emoji}

💰 <b>Current Price:</b> ${price:,}
📊 <b>24h Change:</b> {change_pct:+.2f}%
📈 <b>24h High:</b> ${high:,}
📉 <b>24h Low:</b> ${low:,}

⏰ {now_ist().strftime('%d %b %Y  %H:%M IST')}
<i>Live Updates from Binance ✓</i>"""

    send_telegram(msg)
    print("Telegram alert sent!")
else:
    print("કોઈ મોટો મુવમેન્ટ નથી. સ્કીપ કરાય છે.")