import requests
import os
import pytz
import xml.etree.ElementTree as ET
import time
from datetime import datetime

# ============================================
# CONFIGURATION
# ============================================
BOT_TOKEN = "8874026729:AAEgzZr0UslgaKGdPiUjZMONNuFCKL-pqsY"
CHAT_ID   = "1358803794"

IST = pytz.timezone("Asia/Kolkata")

def now_ist():
    return datetime.now(IST)

# ============================================
# CORE ENGINES (ડેટા, ઇન્ડિકેટર્સ અને ન્યૂઝ લાવવા માટે)
# ============================================
def fetch_live_data(symbol, interval="5m", timeframe_range="2d"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={timeframe_range}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        res = r.json()["chart"]["result"][0]
        closes  = [x for x in res["indicators"]["quote"][0]["close"]  if x is not None]
        highs   = [x for x in res["indicators"]["quote"][0]["high"]   if x is not None]
        volumes = [x for x in res["indicators"]["quote"][0]["volume"] if x is not None]
        price   = res["meta"]["regularMarketPrice"]
        return round(price, 2), closes, highs, volumes
    except:
        return None, [], [], []

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

def fetch_google_news(query):
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(r.text)
        news_items = []
        for item in root.findall(".//item")[:1]: # ટોપ ૧ બ્રેકિંગ ન્યૂઝ
            title = item.find("title").text.split(" - ")[0]
            link = item.find("link").text
            news_items.append(f"• 📰 <b>{title}</b>\n  🔗 <a href='{link}'>વાંચવા માટે ક્લિક કરો</a>")
        return "\n\n📢 <b>LATEST NEWS:</b>\n" + "\n".join(news_items) if news_items else ""
    except:
        return ""

# ============================================
# REPORT BUILDERS (તમારા લોજિક મુજબ મેસેજ ડિઝાઇન)
# ============================================
def get_hbl_report():
    price, closes, highs, volumes = fetch_live_data("HBLENGINE.NS", "5m", "2d")
    if not price: return "❌ HBL નો લાઈવ ડેટા મેળવવામાં ભૂલ થઈ છે."
    rsi = calc_rsi(closes)
    news = fetch_google_news("HBL Power")
    
    # આપણું જૂનું લોજિક ગણતરી (ઇન્ટ્રાડે ₹5)
    t_intra = round(price + 5, 2)
    sl_intra = round(price - 5, 2)
    
    return f"""⚡ <b>HBL POWER SYSTEMS LIVE REPORT</b>

💰 <b>Live Price:</b> ₹{price}
📉 <b>5M RSI:</b> {rsi}
🔥 <b>Logic Target (+₹5):</b> ₹{t_intra}
🛑 <b>Logic Stop Loss (-₹5):</b> ₹{sl_intra}
⏳ <b>Intraday Prediction:</b> Same Day{news}
⏰ {now_ist().strftime('%H:%M:%S IST')}"""

def get_wipro_report():
    price, closes, _, _ = fetch_live_data("WIPRO.NS", "5m", "2d")
    if not price: return "❌ Wipro નો લાઈવ ડેટા મેળવવામાં ભૂલ થઈ છે."
    rsi = calc_rsi(closes)
    news = fetch_google_news("Wipro Buyback")
    
    return f"""💻 <b>WIPRO LIMITED LIVE REPORT</b>

💰 <b>Live Price:</b> ₹{price}
📉 <b>5M RSI:</b> {rsi}
📊 <b>EMA9:</b> {calc_ema(closes, 9)} | <b>EMA21:</b> {calc_ema(closes, 21)}{news}
⏰ {now_ist().strftime('%H:%M:%S IST')}"""

def get_btc_report():
    price, closes, _, volumes = fetch_live_data("BTC-USD", "5m", "2d")
    if not price: return "❌ Bitcoin નો લાઈવ ડેટા મેળવવામાં ભૂલ થઈ છે."
    rsi = calc_rsi(closes)
    news = fetch_google_news("Bitcoin Crypto")
    
    t_btc = round(price + 50, 2)
    sl_btc = round(price - 50, 2)
    
    return f"""🪙 <b>BITCOIN (BTC-USD) LIVE REPORT</b>

💰 <b>Live Price:</b> ${price:,}
📉 <b>5M RSI:</b> {rsi}
🟢 <b>Target (+$50):</b> ${t_btc:,}
🔴 <b>Stop Loss (-$50):</b> ${sl_btc:,}{news}
⏰ {now_ist().strftime('%H:%M:%S IST')}"""

# ============================================
# TELEGRAM BOT INTERACTION MECHANISM
# ============================================
def send_menu():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": "👋 <b>નમસ્તે રવિ!</b>\nતમારો પર્સનલ AI ટ્રેડિંગ એજન્ટ રેડી છે. તમારે ક્યા શેર કે ક્રિપ્ટોની લાઈવ વિગતો જોવી છે? નીચેથી ઓપ્શન પસંદ કરો:",
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "⚡ HBL Power Details", "callback_data": "hbl_data"}],
                [{"text": "💻 Wipro Details", "callback_data": "wipro_data"}],
                [{"text": "🪙 Bitcoin Live Status", "callback_data": "btc_data"}]
            ]
        }
    }
    requests.post(url, json=payload)

def handle_callback(callback_id, data):
    # બટન ક્લિક થાય ત્યારે કયો રિપોર્ટ મોકલવો તે નક્કી કરશે
    if data == "hbl_data": text = get_hbl_report()
    elif data == "wipro_data": text = get_wipro_report()
    elif data == "btc_data": text = get_btc_report()
    else: text = "ભૂલ થઈ છે."
    
    # નવો મેસેજ મોકલો
    url_msg = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url_msg, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})
    
    # ટેલિગ્રામ લોડિંગ આઇકન બંધ કરવા માટે
    url_ans = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    requests.post(url_ans, json={"callback_query_id": callback_id})

# ============================================
# 🚨 MAIN POLLING LOOP (લાઈવ ચેકિંગ ચક્ર)
# ============================================
print("Ravi's Smart Interactive Bot Started...")
offset = 0

# આ લૂપ ૧ મિનિટ સુધી સતત ટેલિગ્રામ પર તમારા મેસેજની રાહ જોશે (ગૂગલ એક્શન રન ટાઈમ માટે સેફ)
start_time = time.time()
while time.time() - start_time < 60:
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=5"
        r = requests.get(url, timeout=10).json()
        
        if "result" in r:
            for update in r["result"]:
                offset = update["update_id"] + 1
                
                # ૧. જો તમે ટેક્સ્ટ મેસેજ મોકલો (દા.ત. Hi, Hello, hbl)
                if "message" in update and "text" in update["message"]:
                    user_msg = update["message"]["text"].lower()
                    if user_msg in ["hi", "hello", "hey", "menu", "hbl", "wipro", "btc"]:
                        send_menu()
                        
                # ૨. જો તમે બટન (Inline Tab) પર ક્લિક કરો
                elif "callback_query" in update:
                    c_id = update["callback_query"]["id"]
                    c_data = update["callback_query"]["data"]
                    handle_callback(c_id, c_data)
    except:
        pass
    time.sleep(1)
