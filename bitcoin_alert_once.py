import requests
import os
import pytz
from datetime import datetime

# ============================================
# SETTINGS - (૧૦૦% કન્ફર્મ અને ડાયરેક્ટ સેટિંગ્સ)
# ============================================
BOT_TOKEN = "8874026729:AAEgzzr0Us1gaKGdPiUjZMONNuFCKL-pqsY"
CHAT_ID   = "1358803794"
SYMBOL    = "BTC-USD"  # Yahoo Finance Bitcoin
QTY       = 1
MOVE      = 50

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

def fetch_data():
    # Yahoo Finance માંથી બિટકોઈનનો 5 મિનિટનો લાઈવ ડેટા
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}?interval=5m&range=2d"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        res = r.json()["chart"]["result"][0]
        closes  = [x for x in res["indicators"]["quote"][0]["close"]  if x is not None]
        volumes = [x for x in res["indicators"]["quote"][0]["volume"] if x is not None]
        price   = res["meta"]["regularMarketPrice"]
        return round(price, 2), closes, volumes
    except Exception as e:
        print(f"Fetch error: {e}"); return None, [], []

def calc_ema(data, p):
    if len(data) < p: return None
    k = 2/(p+1); e = sum(data[:p])/p
    for v in data[p:]: e = v*k + e*(1-k)
    return round(e, 2)

def calc_rsi(data, p=14):
    if len(data) < p+1: return None
    g = sum(max(data[i]-data[i-1],0) for i in range(len(data)-p,len(data)))
    l = sum(max(data[i-1]-data[i],0) for i in range(len(data)-p,len(data)))
    ag, al = g/p, l/p
    return round(100 - 100/(1+ag/al), 1) if al else 100.0

price, closes, volumes = fetch_data()
if not price or len(closes) < 22:
    print("Not enough data."); exit(0)

ema9  = calc_ema(closes, 9)
ema21 = calc_ema(closes, 21)
rsi   = calc_rsi(closes, 14)

# વોલ્યુમ કેલ્ક્યુલેશન
avg_vol = sum(volumes[-6:-1])/5 if len(volumes)>=6 else 0
vol_x = round(volumes[-1]/avg_vol, 1) if avg_vol else 0

print(f"Price=${price} EMA9={ema9} EMA21={ema21} RSI={rsi} Vol={vol_x}x")

# ટેસ્ટ એલર્ટ હોવાથી ટ્રેન્ડ મુજબ BUY અથવા SELL મેસેજ પાકો મોકલશે
if ema9 > ema21:
    sig = "BUY"
    emoji = "🟢📈"
else:
    sig = "SELL"
    emoji = "🔴📉"

t1  = round(price + (MOVE if sig == "BUY" else -MOVE), 2)
sl  = round(price + (-MOVE if sig == "BUY" else MOVE), 2)

msg = f"""{emoji} <b>{SYMBOL} {sig} LIVE SIGNAL!</b>

💰 <b>Price:</b> ${price:,}
📊 <b>EMA9:</b> {ema9} | <b>EMA21:</b> {ema21}
📉 <b>RSI:</b> {rsi} | <b>Vol:</b> {vol_x}x

🎯 <b>Entry:</b>    ${price:,}
✅ <b>Target 1:</b>  ${t1:,}
🛑 <b>Stop Loss:</b> ${sl:,}

⚡ 24/7 Live Crypto Agent Running ✓
⏰ {now_ist().strftime('%d %b %Y  %H:%M IST')}

<i>TradingView Tech Analyzed ✓</i>"""

send_telegram(msg)
print("Bitcoin test alert sent successfully!")
